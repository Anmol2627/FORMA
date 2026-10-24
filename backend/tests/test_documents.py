import io
import fitz  # PyMuPDF


def create_sample_pdf_bytes(page_texts=["Page 1: Study Guide for FORMA"]):
    doc = fitz.open()
    for text in page_texts:
        page = doc.new_page()
        if text:
            page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_upload_valid_pdf_and_extraction(client, auth_headers):
    pdf_bytes = create_sample_pdf_bytes(["Page 1 Content", "Page 2 Content"])
    data = {
        "file": (io.BytesIO(pdf_bytes), "sample_notes.pdf")
    }
    res = client.post(
        "/api/v1/documents",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": auth_headers["Authorization"]}
    )
    assert res.status_code == 201
    doc = res.get_json()["document"]
    assert doc["original_filename"] == "sample_notes.pdf"
    assert doc["page_count"] == 2
    assert doc["processing_status"] == "ready"
    assert "storage_path" not in doc  # Must NOT expose private server path

    doc_id = doc["id"]

    # Retrieve document details
    get_res = client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert get_res.status_code == 200
    details = get_res.get_json()["document"]
    assert len(details["extracted_text_metadata"]) == 2
    assert "Page 1 Content" in details["extracted_text_metadata"][0]["text"]


def test_upload_invalid_file_type(client, auth_headers):
    data = {
        "file": (io.BytesIO(b"Not a PDF"), "document.txt")
    }
    res = client.post(
        "/api/v1/documents",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": auth_headers["Authorization"]}
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "unsupported_file_type"


def test_upload_corrupted_pdf(client, auth_headers):
    corrupt_bytes = b"%PDF-1.4\nInvalid binary junk that cannot be parsed by PyMuPDF"
    data = {
        "file": (io.BytesIO(corrupt_bytes), "corrupt.pdf")
    }
    res = client.post(
        "/api/v1/documents",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": auth_headers["Authorization"]}
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] in ["invalid_pdf_format", "pdf_processing_error"]


def test_upload_empty_text_pdf(client, auth_headers):
    # PDF with a blank page (like a scanned PDF without OCR)
    pdf_bytes = create_sample_pdf_bytes([""])
    data = {
        "file": (io.BytesIO(pdf_bytes), "blank_scan.pdf")
    }
    res = client.post(
        "/api/v1/documents",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": auth_headers["Authorization"]}
    )
    assert res.status_code == 201
    doc = res.get_json()["document"]
    assert doc["page_count"] == 1


def test_document_ownership_enforcement(client, auth_headers, other_user_headers):
    pdf_bytes = create_sample_pdf_bytes()
    data = {
        "file": (io.BytesIO(pdf_bytes), "private_notes.pdf")
    }
    res = client.post(
        "/api/v1/documents",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": auth_headers["Authorization"]}
    )
    doc_id = res.get_json()["document"]["id"]

    # Secondary user lists documents -> doc_id not in list
    list_res = client.get("/api/v1/documents", headers=other_user_headers)
    assert list_res.status_code == 200
    docs = list_res.get_json()["documents"]
    assert doc_id not in [d["id"] for d in docs]

    # Secondary user attempts to get doc -> 403 Forbidden
    get_res = client.get(f"/api/v1/documents/{doc_id}", headers=other_user_headers)
    assert get_res.status_code == 403
    assert get_res.get_json()["error"]["code"] == "forbidden_document_access"

    # Secondary user attempts to delete doc -> 403 Forbidden
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=other_user_headers)
    assert del_res.status_code == 403

    # Primary owner deletes doc -> 200 OK
    del_ok = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert del_ok.status_code == 200
