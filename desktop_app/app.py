import os
import re
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

# Ensure project root and desktop_app are in sys.path for direct execution
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

try:
    from .config import (
        APP_NAME,
        MIN_HEIGHT,
        MIN_WIDTH,
        WINDOW_HEIGHT,
        WINDOW_TITLE,
        WINDOW_WIDTH,
    )
    from .services import api_client
    from .theme import COLORS, FONT
except (ImportError, ValueError):
    from config import (
        APP_NAME,
        MIN_HEIGHT,
        MIN_WIDTH,
        WINDOW_HEIGHT,
        WINDOW_TITLE,
        WINDOW_WIDTH,
    )
    import services.api_client as api_client
    from theme import COLORS, FONT


class FormaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.configure(bg=COLORS["background"])

        self.current_user = None
        self.access_token = None
        self.active_quiz = None
        self.active_chat_session = None
        self.quiz_answer_vars = {}
        self.sidebar_buttons = {}
        self.profile_menu = None

        self._build_shell()
        self.show_page("Explore Quizzes")

    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=210)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        brand.pack(fill="x", padx=22, pady=(20, 26))
        tk.Label(
            brand, text="✿", font=(FONT, 24, "bold"), fg=COLORS["violet"],
            bg=COLORS["sidebar"]
        ).pack(side="left", padx=(0, 9))
        tk.Label(
            brand, text=APP_NAME, font=(FONT, 19, "bold"), fg=COLORS["ink"],
            bg=COLORS["sidebar"]
        ).pack(side="left")

        nav_items = [
            ("⌂", "Home"),
            ("◉", "Explore Quizzes"),
            ("＋", "Create Quiz"),
            ("▤", "Ask Your PDF"),
            ("♧", "My Quizzes"),
            ("▥", "Progress"),
        ]
        self.nav_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        self.nav_frame.pack(fill="x", padx=12)
        for symbol, name in nav_items:
            button = tk.Button(
                self.nav_frame, text=f"  {symbol}     {name}", anchor="w",
                font=(FONT, 10), relief="flat", bd=0, cursor="hand2",
                padx=10, pady=11, command=lambda page=name: self.show_page(page),
                bg=COLORS["sidebar"], fg=COLORS["ink"],
                activebackground=COLORS["violet_light"], activeforeground=COLORS["ink"]
            )
            button.pack(fill="x", pady=2)
            self.sidebar_buttons[name] = button

        spacer = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        spacer.pack(fill="both", expand=True)
        tk.Label(
            self.sidebar, text="🐾  Small steps\n     Big progress", justify="left",
            font=(FONT, 10, "italic"), fg=COLORS["muted"],
            bg=COLORS["sidebar"]
        ).pack(padx=22, pady=18, anchor="w")
        tk.Button(
            self.sidebar, text="⚙     Settings", anchor="w", font=(FONT, 10),
            relief="flat", bd=0, cursor="hand2", padx=22, pady=14,
            bg=COLORS["sidebar"], fg=COLORS["ink"],
            command=lambda: self.show_page("Settings")
        ).pack(fill="x", side="bottom", padx=12, pady=(0, 10))

        self.main = tk.Frame(self, bg=COLORS["background"])
        self.main.pack(side="left", fill="both", expand=True)

        self.topbar = tk.Frame(self.main, bg=COLORS["background"])
        self.topbar.pack(fill="x", padx=30, pady=(14, 10))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            self.topbar, textvariable=self.search_var, font=(FONT, 10),
            relief="solid", bd=1, highlightthickness=0,
            bg=COLORS["surface"], fg=COLORS["ink"]
        )
        self.search_entry.insert(0, "Search for quizzes, topics or subjects...")
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 18))
        tk.Label(
            self.topbar, text="♧", font=(FONT, 17), bg=COLORS["background"],
            fg=COLORS["ink"]
        ).pack(side="left", padx=12)
        self.profile_button = tk.Button(
            self.topbar, text="◉  Sign in / Sign up  ⌄", font=(FONT, 10, "bold"),
            relief="flat", bd=0, cursor="hand2", bg=COLORS["background"],
            fg=COLORS["ink"], activebackground=COLORS["violet_light"],
            command=self.toggle_profile_menu
        )
        self.profile_button.pack(side="left", padx=(5, 0))
        self.profile_menu = tk.Frame(
            self.main, bg=COLORS["surface"],
            highlightbackground=COLORS["border"], highlightthickness=1
        )

        self.content = tk.Frame(self.main, bg=COLORS["background"])
        self.content.pack(fill="both", expand=True, padx=30, pady=(0, 12))
        self._update_profile_button()

    def _update_profile_button(self):
        if self.current_user:
            display = self.current_user.get("display_name", "Student")
            self.profile_button.configure(text=f"◉  {display}  ⌄")
        else:
            self.profile_button.configure(text="◉  Sign in / Sign up  ⌄")

    def toggle_profile_menu(self):
        if self.profile_menu.winfo_manager():
            self.profile_menu.place_forget()
            return

        for child in self.profile_menu.winfo_children():
            child.destroy()

        options = (
            [
                ("My profile", lambda: self.show_page("Profile")),
                ("Log out", self.logout),
            ]
            if self.current_user
            else [
                ("Sign in", lambda: self.show_page("Sign in")),
                ("Create an account", lambda: self.show_page("Sign up")),
            ]
        )

        for label, callback in options:
            button = tk.Button(
                self.profile_menu,
                text=label,
                anchor="w",
                font=(FONT, 10),
                relief="flat",
                bd=0,
                padx=14,
                pady=10,
                bg=COLORS["surface"],
                fg=COLORS["ink"],
                activebackground=COLORS["violet_light"],
                activeforeground=COLORS["ink"],
                cursor="hand2",
                command=lambda cb=callback: self._menu_action(cb),
            )
            button.pack(fill="x")

        self.profile_menu.update_idletasks()
        self.profile_menu.lift()
        self.profile_menu.place(
            relx=1.0,
            x=-5,
            y=52,
            anchor="ne",
        )

    def _menu_action(self, command):
        self.profile_menu.place_forget()
        command()

    def show_page(self, page):
        if self.profile_menu.winfo_manager():
            self.profile_menu.place_forget()
        for name, button in self.sidebar_buttons.items():
            button.configure(
                bg=COLORS["violet_light"] if name == page else COLORS["sidebar"],
                fg=COLORS["ink"]
            )
        for widget in self.content.winfo_children():
            widget.destroy()

        if page == "Home":
            self._build_home()
        elif page == "Explore Quizzes":
            self._build_explore()
        elif page == "Create Quiz":
            self._build_create_quiz()
        elif page == "Ask Your PDF":
            self._build_ask_your_pdf()
        elif page == "My Quizzes":
            self._build_my_quizzes()
        elif page == "Progress":
            self._build_progress()
        elif page == "Take Quiz":
            self._build_take_quiz()
        elif page == "Sign in":
            self._build_auth("Sign in")
        elif page == "Sign up":
            self._build_auth("Sign up")
        elif page == "Profile":
            self._build_profile()
        elif page == "Settings":
            self._build_settings()
        else:
            self._build_placeholder(page)

    def _require_login(self, action_name: str) -> bool:
        if self.current_user and self.access_token:
            return True
        messagebox.showinfo("Sign in required", f"Please sign in or create an account to {action_name}.")
        self.show_page("Sign in")
        return False

    # -------------------------------------------------------------------------
    # Authentication & Profile Views
    # -------------------------------------------------------------------------

    def _build_auth(self, mode):
        panel = tk.Frame(self.content, bg=COLORS["background"])
        panel.pack(fill="both", expand=True, anchor="n")
        card = tk.Frame(
            panel, bg=COLORS["surface"], highlightbackground=COLORS["border"],
            highlightthickness=1, padx=34, pady=28, width=430
        )
        card.pack(anchor="n", pady=30)

        tk.Label(card, text="✿  FORMA", font=(FONT, 13, "bold"),
                 bg=COLORS["surface"], fg=COLORS["violet"]).pack(anchor="w")
        tk.Label(card, text=mode, font=(FONT, 25, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w", pady=(16, 4))
        subtitle = (
            "Welcome back! Sign in to continue learning."
            if mode == "Sign in"
            else "Create an account and make every step count."
        )
        tk.Label(card, text=subtitle, font=(FONT, 10), bg=COLORS["surface"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 20))

        name_var = tk.StringVar()
        email_var = tk.StringVar()
        password_var = tk.StringVar()
        confirm_var = tk.StringVar()

        if mode == "Sign up":
            self._field(card, "Display name", name_var)
        self._field(card, "Email address", email_var)
        self._field(card, "Password", password_var, show="•")
        if mode == "Sign up":
            self._field(card, "Confirm password", confirm_var, show="•")

        def submit():
            display_name = name_var.get().strip()
            email = email_var.get().strip().lower()
            password = password_var.get()

            if not email or not password:
                messagebox.showwarning("Missing details", "Please enter your email and password.")
                return

            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                messagebox.showwarning("Invalid email", "Enter a valid email address.")
                return

            if len(password) < 8:
                messagebox.showwarning("Password too short", "Use at least 8 characters.")
                return

            if mode == "Sign up":
                if not display_name:
                    messagebox.showwarning("Missing name", "Please enter a display name.")
                    return

                if password != confirm_var.get():
                    messagebox.showwarning("Passwords don't match", "Please make sure both passwords match.")
                    return

            try:
                if mode == "Sign up":
                    response = api_client.register(display_name, email, password)
                else:
                    response = api_client.login(email, password)

                user = response.get("user")
                token = response.get("access_token")

                if not user or not token:
                    messagebox.showerror(
                        "Authentication error",
                        "The backend did not return the expected account details."
                    )
                    return

                self.current_user = user
                self.access_token = token
                self._update_profile_button()

                messagebox.showinfo("Success", f"Welcome, {user.get('display_name', 'Student')}!")
                self.show_page("Explore Quizzes")

            except api_client.APIError as exc:
                messagebox.showerror("Authentication failed", str(exc))

        tk.Button(
            card,
            text=mode,
            font=(FONT, 10, "bold"),
            bg=COLORS["violet"],
            fg="white",
            activebackground=COLORS["violet"],
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=11,
            command=submit,
        ).pack(fill="x", pady=(18, 10))

        switch_text = (
            "Don't have an account? Sign up"
            if mode == "Sign in"
            else "Already have an account? Sign in"
        )
        switch_target = "Sign up" if mode == "Sign in" else "Sign in"

        tk.Button(
            card,
            text=switch_text,
            font=(FONT, 9),
            bg=COLORS["surface"],
            fg=COLORS["violet"],
            activebackground=COLORS["violet_light"],
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda: self.show_page(switch_target),
        ).pack(anchor="center")

        tk.Label(
            card,
            text="Secured via FORMA REST API & JWT",
            font=(FONT, 8),
            bg=COLORS["surface"],
            fg=COLORS["muted"],
        ).pack(pady=(14, 0))

    def _field(self, parent, label, variable, show=None):
        tk.Label(parent, text=label, font=(FONT, 9, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w", pady=(8, 5))
        entry = tk.Entry(parent, textvariable=variable, font=(FONT, 10),
                         relief="solid", bd=1, highlightthickness=0,
                         bg="#FFFFFF", fg=COLORS["ink"], show=show or "")
        entry.pack(fill="x", ipady=7)
        return entry

    def _build_profile(self):
        if not self.current_user:
            self._build_auth("Sign in")
            return
        tk.Label(self.content, text="My profile", font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(25, 12))
        card = tk.Frame(
            self.content, bg=COLORS["surface"], padx=24, pady=22,
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        card.pack(anchor="nw", fill="x")
        tk.Label(card, text=self.current_user.get("display_name", "Student"), font=(FONT, 17, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w")
        tk.Label(card, text=self.current_user.get("email", ""), font=(FONT, 10),
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor="w", pady=(4, 6))

        status = self.current_user.get("account_status", "active")
        tk.Label(card, text=f"Account Status: {status.upper()}", font=(FONT, 9, "bold"),
                 bg=COLORS["surface"], fg=COLORS["green_text"]).pack(anchor="w", pady=(0, 16))

        tk.Button(card, text="Log out", font=(FONT, 10, "bold"), bg=COLORS["violet"],
                  fg="white", relief="flat", padx=16, pady=8, cursor="hand2",
                  command=self.logout).pack(anchor="w")

    def logout(self):
        self.current_user = None
        self.access_token = None
        self.active_quiz = None
        self.active_chat_session = None
        self._update_profile_button()
        self.show_page("Explore Quizzes")
        messagebox.showinfo("Signed out", "You have been signed out.")

    # -------------------------------------------------------------------------
    # Home & Explore Views
    # -------------------------------------------------------------------------

    def _build_home(self):
        heading = tk.Frame(self.content, bg=COLORS["background"])
        heading.pack(fill="x", pady=(12, 16))

        greeting = (
            f"Welcome back, {self.current_user['display_name']}!"
            if self.current_user
            else "Welcome to FORMA!"
        )
        tk.Label(heading, text=greeting, font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w")
        tk.Label(
            heading,
            text="Practice quizzes, understand mistakes, study from PDFs, and track your learning progress.",
            font=(FONT, 11), bg=COLORS["background"], fg=COLORS["muted"]
        ).pack(anchor="w", pady=(2, 0))

        cards_area = tk.Frame(self.content, bg=COLORS["background"])
        cards_area.pack(fill="both", expand=True, pady=10)

        dash_cards = [
            ("◉", "Explore Quizzes", "Browse curated subjects and tests.", "Explore Quizzes", COLORS["violet_light"]),
            ("＋", "Create a Quiz", "Create custom quizzes or use AI.", "Create Quiz", COLORS["mint"]),
            ("▤", "Ask Your PDF", "Upload study PDFs and ask questions.", "Ask Your PDF", COLORS["blue"]),
            ("▥", "View Progress", "See your accuracy and score history.", "Progress", COLORS["butter"]),
        ]

        for col in range(2):
            cards_area.grid_columnconfigure(col, weight=1, uniform="dash")
        for row in range(2):
            cards_area.grid_rowconfigure(row, weight=1, uniform="dash")

        for index, (symbol, title, description, target_page, icon_bg) in enumerate(dash_cards):
            row, col = divmod(index, 2)
            card = tk.Frame(
                cards_area, bg=COLORS["surface"], highlightbackground=COLORS["border"],
                highlightthickness=1, padx=22, pady=18
            )
            card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            tk.Label(card, text=symbol, font=(FONT, 22, "bold"), width=3, pady=4,
                     bg=icon_bg, fg=COLORS["ink"]).pack(anchor="w")
            tk.Label(card, text=title, font=(FONT, 13, "bold"), bg=COLORS["surface"],
                     fg=COLORS["ink"]).pack(anchor="w", pady=(10, 4))
            tk.Label(card, text=description, font=(FONT, 10), bg=COLORS["surface"],
                     fg=COLORS["muted"]).pack(anchor="w")
            tk.Button(
                card, text="Open  →", font=(FONT, 10, "bold"), bg=COLORS["violet_light"],
                fg=COLORS["ink"], relief="flat", padx=12, pady=6, cursor="hand2",
                command=lambda p=target_page: self.show_page(p)
            ).pack(anchor="e", pady=(14, 0))

    def _build_explore(self):
        heading = tk.Frame(self.content, bg=COLORS["background"])
        heading.pack(fill="x", pady=(6, 12))
        tk.Label(heading, text="Explore quizzes", font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w")
        tk.Label(heading, text="Practice curated quizzes across subjects and topics.",
                 font=(FONT, 11), bg=COLORS["background"], fg=COLORS["muted"]).pack(anchor="w", pady=(2, 0))

        filters = tk.Frame(self.content, bg=COLORS["background"])
        filters.pack(fill="x", pady=(4, 15))
        for i, label in enumerate(["All", "DBMS", "Operating Systems", "Data Structures", "OOP", "Networks", "System Design"]):
            active = (i == 0)
            tk.Button(
                filters, text=label, font=(FONT, 9), relief="flat", bd=0,
                padx=13, pady=7, cursor="hand2",
                bg=COLORS["violet"] if active else COLORS["surface"],
                fg="white" if active else COLORS["ink"],
                activebackground=COLORS["violet_light"],
                command=lambda value=label: self._filter_notice(value)
            ).pack(side="left", padx=(0, 7))

        cards_area = tk.Frame(self.content, bg=COLORS["background"])
        cards_area.pack(fill="both", expand=True)
        subjects = [
            ("▤", "DBMS", "Practice database concepts\nwith curated questions.", "120 questions", "Medium", COLORS["violet_light"]),
            ("▱", "Operating Systems", "Process management, memory,\nscheduling and more.", "85 questions", "Medium", COLORS["mint"]),
            ("⬡", "Data Structures", "Arrays, linked lists, trees,\ngraphs and more.", "110 questions", "Medium", COLORS["red_light"]),
            ("∞", "OOP Concepts", "Learn object oriented\nprogramming concepts.", "95 questions", "Easy", COLORS["mint"]),
            ("⌁", "Computer Networks", "Protocols, layers, routing\nand network basics.", "70 questions", "Medium", COLORS["blue"]),
            ("◇", "System Design", "Scalable system design\nconcepts and case studies.", "60 questions", "Hard", COLORS["red_light"]),
            ("∑", "Discrete Mathematics", "Logic, sets, combinatorics\nand more.", "80 questions", "Medium", COLORS["violet_light"]),
            ("▥", "Aptitude & Logic", "Quantitative aptitude\nand logical reasoning.", "90 questions", "Easy", COLORS["mint"]),
            ("▦", "More Subjects", "AI, Web Development, Cybersecurity\nand other topics.", "Explore all", "", COLORS["butter"]),
        ]
        for col in range(3):
            cards_area.grid_columnconfigure(col, weight=1, uniform="cards")
        for row in range(3):
            cards_area.grid_rowconfigure(row, weight=1, uniform="rows")

        for index, (symbol, title, description, count, level, icon_bg) in enumerate(subjects):
            row, col = divmod(index, 3)
            card = tk.Frame(
                cards_area, bg=COLORS["surface"], highlightbackground=COLORS["border"],
                highlightthickness=1, padx=15, pady=11
            )
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            tk.Label(card, text=symbol, font=(FONT, 19, "bold"), width=3, pady=2,
                     bg=icon_bg, fg=COLORS["ink"]).pack(anchor="w")
            tk.Label(card, text=title, font=(FONT, 11, "bold"), bg=COLORS["surface"],
                     fg=COLORS["ink"]).pack(anchor="w", pady=(6, 2))
            tk.Label(card, text=description, justify="left", anchor="w", font=(FONT, 9),
                     bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor="w", fill="x")
            bottom = tk.Frame(card, bg=COLORS["surface"])
            bottom.pack(fill="x", side="bottom", pady=(6, 0))
            tk.Label(bottom, text=count, font=(FONT, 8), bg=COLORS["surface"],
                     fg=COLORS["muted"]).pack(side="left")
            if level:
                badge_bg, badge_fg = {
                    "Easy": (COLORS["mint"], COLORS["green_text"]),
                    "Medium": (COLORS["butter"], COLORS["orange_text"]),
                    "Hard": (COLORS["red_light"], COLORS["red_text"]),
                }[level]
                tk.Label(bottom, text=f" {level} ", font=(FONT, 8), bg=badge_bg,
                         fg=badge_fg).pack(side="left", padx=8)
            tk.Button(
                bottom, text="→", font=(FONT, 11, "bold"), relief="flat", bd=0,
                bg=COLORS["surface"], fg=COLORS["ink"], cursor="hand2",
                command=lambda subject=title: self._open_subject(subject)
            ).pack(side="right")

    def _filter_notice(self, subject):
        if subject == "All":
            self._open_subject("All Available Quizzes")
        else:
            self._open_subject(subject)

    def _open_subject(self, subject):
        if not self.access_token:
            messagebox.showinfo("Sign in required", "Please sign in to view and practice available quizzes.")
            self.show_page("Sign in")
            return

        for widget in self.content.winfo_children():
            widget.destroy()

        header = tk.Frame(self.content, bg=COLORS["background"])
        header.pack(fill="x", pady=(14, 8))
        tk.Label(header, text=subject, font=(FONT, 25, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(side="left")
        tk.Button(
            header, text="← Back to Explore", font=(FONT, 10),
            bg=COLORS["surface"], fg=COLORS["ink"], relief="flat", padx=12, pady=6,
            command=lambda: self.show_page("Explore Quizzes")
        ).pack(side="right")

        try:
            response = api_client.get_quizzes(self.access_token, include_public=True)
            quizzes = response.get("quizzes", [])
        except api_client.APIError as exc:
            messagebox.showerror("Could not load quizzes", str(exc))
            return

        if not quizzes:
            tk.Label(
                self.content,
                text="No quizzes found in this category. You can create a quiz or generate one with AI!",
                font=(FONT, 11), bg=COLORS["background"], fg=COLORS["muted"]
            ).pack(anchor="w", pady=20)

            tk.Button(
                self.content, text="+ Create or Generate Quiz", font=(FONT, 10, "bold"),
                bg=COLORS["violet"], fg="white", relief="flat", padx=16, pady=8,
                command=lambda: self.show_page("Create Quiz")
            ).pack(anchor="w")
            return

        for quiz in quizzes:
            card = tk.Frame(
                self.content, bg=COLORS["surface"], padx=18, pady=14,
                highlightbackground=COLORS["border"], highlightthickness=1
            )
            card.pack(fill="x", pady=6)

            info = tk.Frame(card, bg=COLORS["surface"])
            info.pack(side="left", fill="x", expand=True)

            tk.Label(
                info, text=quiz.get("title", "Untitled Quiz"),
                font=(FONT, 12, "bold"), bg=COLORS["surface"], fg=COLORS["ink"]
            ).pack(anchor="w")

            desc = quiz.get("description") or "Ready to practice"
            q_count = quiz.get("question_count", 0)
            vis = quiz.get("visibility", "public").capitalize()
            tk.Label(
                info, text=f"{q_count} questions  ·  {vis}  ·  {desc}",
                font=(FONT, 9), bg=COLORS["surface"], fg=COLORS["muted"], wraplength=700
            ).pack(anchor="w", pady=(4, 0))

            tk.Button(
                card, text="Take quiz  →", font=(FONT, 9, "bold"),
                bg=COLORS["violet_light"], fg=COLORS["ink"], relief="flat",
                padx=14, pady=8, cursor="hand2",
                command=lambda qid=quiz["id"]: self._start_quiz(qid)
            ).pack(side="right")

    # -------------------------------------------------------------------------
    # Quiz Creation (Manual + AI Generation)
    # -------------------------------------------------------------------------

    def _build_create_quiz(self):
        if not self._require_login("create a quiz"):
            return

        tk.Label(self.content, text="Create a quiz", font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(16, 4))
        tk.Label(
            self.content,
            text="Choose manual question building or generate questions automatically with AI.",
            font=(FONT, 10), bg=COLORS["background"], fg=COLORS["muted"]
        ).pack(anchor="w", pady=(0, 12))

        # Mode Selector Buttons
        mode_frame = tk.Frame(self.content, bg=COLORS["background"])
        mode_frame.pack(fill="x", pady=(0, 12))

        form_container = tk.Frame(self.content, bg=COLORS["background"])
        form_container.pack(fill="both", expand=True)

        def switch_mode(mode):
            for w in form_container.winfo_children():
                w.destroy()
            if mode == "manual":
                manual_btn.configure(bg=COLORS["violet"], fg="white")
                ai_btn.configure(bg=COLORS["surface"], fg=COLORS["ink"])
                self._render_manual_quiz_form(form_container)
            else:
                ai_btn.configure(bg=COLORS["violet"], fg="white")
                manual_btn.configure(bg=COLORS["surface"], fg=COLORS["ink"])
                self._render_ai_quiz_form(form_container)

        manual_btn = tk.Button(
            mode_frame, text="✍  Manual Creation", font=(FONT, 10, "bold"),
            relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
            bg=COLORS["violet"], fg="white",
            command=lambda: switch_mode("manual")
        )
        manual_btn.pack(side="left", padx=(0, 8))

        ai_btn = tk.Button(
            mode_frame, text="✨  Generate with AI", font=(FONT, 10, "bold"),
            relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
            bg=COLORS["surface"], fg=COLORS["ink"],
            command=lambda: switch_mode("ai")
        )
        ai_btn.pack(side="left")

        # Initial render: manual form
        self._render_manual_quiz_form(form_container)

    def _render_manual_quiz_form(self, container):
        form = tk.Frame(
            container, bg=COLORS["surface"], padx=20, pady=18,
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        form.pack(fill="x", anchor="n")

        title_var = tk.StringVar()
        desc_var = tk.StringVar()
        vis_var = tk.StringVar(value="public")

        self._simple_field(form, "Quiz title", title_var)
        self._simple_field(form, "Description (optional)", desc_var)

        vis_row = tk.Frame(form, bg=COLORS["surface"])
        vis_row.pack(fill="x", pady=(6, 10))
        tk.Label(vis_row, text="Visibility: ", font=(FONT, 9, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(side="left")
        tk.Radiobutton(vis_row, text="Public", variable=vis_var, value="public",
                       bg=COLORS["surface"]).pack(side="left", padx=10)
        tk.Radiobutton(vis_row, text="Private", variable=vis_var, value="private",
                       bg=COLORS["surface"]).pack(side="left")

        q_frame = tk.Frame(form, bg=COLORS["surface"])
        q_frame.pack(fill="x", pady=(10, 0))
        tk.Label(q_frame, text="Question 1", font=(FONT, 12, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w")

        prompt_var = tk.StringVar()
        self._simple_field(q_frame, "Question prompt", prompt_var)

        option_vars = [tk.StringVar() for _ in range(4)]
        correct_var = tk.IntVar(value=0)

        tk.Label(
            q_frame, text="Answer options (select the radio button next to the correct answer)",
            font=(FONT, 9, "bold"), bg=COLORS["surface"], fg=COLORS["ink"]
        ).pack(anchor="w", pady=(8, 4))

        for i, var in enumerate(option_vars):
            line = tk.Frame(q_frame, bg=COLORS["surface"])
            line.pack(fill="x", pady=3)
            tk.Radiobutton(line, variable=correct_var, value=i, bg=COLORS["surface"],
                           activebackground=COLORS["surface"]).pack(side="left")
            tk.Entry(line, textvariable=var, font=(FONT, 10), relief="solid", bd=1,
                     bg="#FFFFFF").pack(side="left", fill="x", expand=True, ipady=5)

        explanation_var = tk.StringVar()
        self._simple_field(q_frame, "Explanation shown after answering (optional)", explanation_var)

        def save():
            title = title_var.get().strip()
            prompt = prompt_var.get().strip()
            options = [v.get().strip() for v in option_vars]

            if not title or not prompt or any(not value for value in options):
                messagebox.showwarning(
                    "Missing details",
                    "Enter a quiz title, question prompt, and all 4 options."
                )
                return

            questions = [{
                "prompt": prompt,
                "explanation": explanation_var.get().strip() or None,
                "options": [
                    {
                        "option_text": option,
                        "is_correct": (index == correct_var.get())
                    }
                    for index, option in enumerate(options)
                ]
            }]

            try:
                api_client.create_quiz(
                    title=title,
                    description=desc_var.get().strip(),
                    questions=questions,
                    token=self.access_token,
                    visibility=vis_var.get(),
                )
                messagebox.showinfo("Quiz saved", "Your quiz has been saved successfully!")
                self.show_page("My Quizzes")
            except api_client.APIError as exc:
                messagebox.showerror("Could not save quiz", str(exc))

        tk.Button(
            form, text="Save Quiz", font=(FONT, 11, "bold"),
            bg=COLORS["violet"], fg="#FFFFFF", relief="flat",
            padx=24, pady=10, cursor="hand2", command=save
        ).pack(anchor="e", pady=(16, 0))

    def _render_ai_quiz_form(self, container):
        card = tk.Frame(
            container, bg=COLORS["surface"], padx=20, pady=18,
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        card.pack(fill="x", anchor="n")

        topic_var = tk.StringVar()
        count_var = tk.IntVar(value=5)
        diff_var = tk.StringVar(value="medium")

        self._simple_field(card, "Academic Topic or Subject", topic_var)

        options_row = tk.Frame(card, bg=COLORS["surface"])
        options_row.pack(fill="x", pady=(10, 8))

        # Question Count
        tk.Label(options_row, text="Questions Count (1-20):", font=(FONT, 9, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(side="left", padx=(0, 10))
        tk.Spinbox(options_row, from_=1, to=20, textvariable=count_var, width=5,
                   font=(FONT, 10)).pack(side="left", padx=(0, 24))

        # Difficulty
        tk.Label(options_row, text="Difficulty:", font=(FONT, 9, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(side="left", padx=(0, 10))
        for level in ["easy", "medium", "hard"]:
            tk.Radiobutton(options_row, text=level.capitalize(), variable=diff_var, value=level,
                           bg=COLORS["surface"]).pack(side="left", padx=5)

        tk.Label(card, text="Reference Lecture Notes / Source Text (Optional):", font=(FONT, 9, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w", pady=(12, 4))
        notes_text = tk.Text(card, height=6, font=(FONT, 10), relief="solid", bd=1)
        notes_text.pack(fill="x")

        status_label = tk.Label(card, text="", font=(FONT, 9, "italic"),
                                bg=COLORS["surface"], fg=COLORS["violet"])
        status_label.pack(anchor="w", pady=(8, 0))

        def generate():
            topic = topic_var.get().strip()
            if not topic:
                messagebox.showwarning("Missing topic", "Please specify a topic for AI generation.")
                return

            notes = notes_text.get("1.0", tk.END).strip()
            status_label.configure(text="Generating questions with AI... Please wait.")
            self.update_idletasks()

            try:
                response = api_client.generate_ai_quiz(
                    topic=topic,
                    question_count=count_var.get(),
                    difficulty=diff_var.get(),
                    source_text=notes if notes else None,
                    token=self.access_token,
                )
                status_label.configure(text="")
                quiz = response.get("quiz", {})
                messagebox.showinfo(
                    "AI Quiz Generated",
                    f"Successfully generated '{quiz.get('title')}' with {quiz.get('question_count', 0)} questions!"
                )
                self.show_page("My Quizzes")

            except api_client.APIError as exc:
                status_label.configure(text="")
                messagebox.showerror("AI Generation Error", str(exc))

        tk.Button(
            card, text="✨  Generate Quiz with AI", font=(FONT, 11, "bold"),
            bg=COLORS["violet"], fg="#FFFFFF", relief="flat",
            padx=24, pady=10, cursor="hand2", command=generate
        ).pack(anchor="e", pady=(16, 0))

    def _simple_field(self, parent, label, variable):
        tk.Label(parent, text=label, font=(FONT, 9, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w", pady=(7, 4))
        entry = tk.Entry(parent, textvariable=variable, font=(FONT, 10),
                         relief="solid", bd=1, bg="#FFFFFF", fg=COLORS["ink"])
        entry.pack(fill="x", ipady=6)
        return entry

    # -------------------------------------------------------------------------
    # My Quizzes View
    # -------------------------------------------------------------------------

    def _build_my_quizzes(self):
        if not self._require_login("view your quizzes"):
            return

        header = tk.Frame(self.content, bg=COLORS["background"])
        header.pack(fill="x", pady=(18, 14))

        tk.Label(
            header, text="My quizzes", font=(FONT, 27, "bold"),
            bg=COLORS["background"], fg=COLORS["ink"]
        ).pack(side="left")

        tk.Button(
            header, text="+ Create quiz", font=(FONT, 10, "bold"),
            bg=COLORS["violet"], fg="white", relief="flat",
            padx=14, pady=8, cursor="hand2",
            command=lambda: self.show_page("Create Quiz")
        ).pack(side="right")

        try:
            response = api_client.get_quizzes(self.access_token, include_public=False)
            quizzes = response.get("quizzes", [])
        except api_client.APIError as exc:
            messagebox.showerror("Could not load quizzes", str(exc))
            return

        if not quizzes:
            tk.Label(
                self.content,
                text="Your quiz library is empty for now.",
                font=(FONT, 12), bg=COLORS["background"], fg=COLORS["muted"]
            ).pack(anchor="w", pady=20)

            tk.Label(
                self.content,
                text="Create your first quiz manually or with AI to see it here.",
                font=(FONT, 10), bg=COLORS["background"], fg=COLORS["muted"]
            ).pack(anchor="w")
            return

        for quiz in quizzes:
            card = tk.Frame(
                self.content, bg=COLORS["surface"], padx=18, pady=13,
                highlightbackground=COLORS["border"], highlightthickness=1
            )
            card.pack(fill="x", pady=5)

            info = tk.Frame(card, bg=COLORS["surface"])
            info.pack(side="left", fill="x", expand=True)

            tk.Label(
                info, text=quiz.get("title", "Untitled quiz"),
                font=(FONT, 12, "bold"), bg=COLORS["surface"], fg=COLORS["ink"]
            ).pack(anchor="w")

            description = quiz.get("description") or "No description"
            count = quiz.get("question_count", 0)
            vis = quiz.get("visibility", "private").capitalize()

            tk.Label(
                info, text=f"{count} question(s)  ·  {vis}  ·  {description}",
                font=(FONT, 9), bg=COLORS["surface"], fg=COLORS["muted"]
            ).pack(anchor="w", pady=(4, 0))

            btn_frame = tk.Frame(card, bg=COLORS["surface"])
            btn_frame.pack(side="right")

            tk.Button(
                btn_frame, text="Take quiz  →", font=(FONT, 9, "bold"),
                bg=COLORS["violet_light"], fg=COLORS["ink"], relief="flat",
                padx=12, pady=7, cursor="hand2",
                command=lambda qid=quiz["id"]: self._start_quiz(qid)
            ).pack(side="left", padx=(0, 6))

            tk.Button(
                btn_frame, text="Delete ✕", font=(FONT, 9),
                bg=COLORS["surface"], fg=COLORS["red_text"], relief="flat",
                padx=8, pady=7, cursor="hand2",
                command=lambda qid=quiz["id"]: self._delete_quiz(qid)
            ).pack(side="left")

    def _delete_quiz(self, quiz_id: str):
        if not messagebox.askyesno("Confirm deletion", "Are you sure you want to delete this quiz?"):
            return
        try:
            api_client.delete_quiz(quiz_id, self.access_token)
            messagebox.showinfo("Quiz deleted", "Quiz deleted successfully.")
            self._build_my_quizzes()
        except api_client.APIError as exc:
            messagebox.showerror("Deletion failed", str(exc))

    # -------------------------------------------------------------------------
    # Quiz Taking & Results View (Security Boundary Preserved)
    # -------------------------------------------------------------------------

    def _start_quiz(self, quiz_id):
        if not self.access_token:
            messagebox.showinfo("Sign in required", "Please sign in first to take quizzes.")
            self.show_page("Sign in")
            return

        try:
            response = api_client.get_quiz_to_take(quiz_id, self.access_token)
            self.active_quiz = response.get("quiz")
            self.quiz_answer_vars = {}
            self.show_page("Take Quiz")
        except api_client.APIError as exc:
            messagebox.showerror("Could not open quiz", str(exc))

    def _build_take_quiz(self):
        quiz = self.active_quiz
        if not quiz or not quiz.get("questions"):
            self._build_placeholder("Take Quiz")
            return

        tk.Label(self.content, text=quiz.get("title", "Quiz"), font=(FONT, 25, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(14, 4))
        tk.Label(self.content, text="Choose one answer for each question, then submit for server scoring.",
                 font=(FONT, 10), bg=COLORS["background"], fg=COLORS["muted"]).pack(anchor="w", pady=(0, 12))

        for idx, question in enumerate(quiz["questions"]):
            card = tk.Frame(
                self.content, bg=COLORS["surface"], padx=18, pady=12,
                highlightbackground=COLORS["border"], highlightthickness=1
            )
            card.pack(fill="x", pady=6)

            tk.Label(card, text=f'{idx + 1}. {question["prompt"]}', font=(FONT, 11, "bold"),
                     bg=COLORS["surface"], fg=COLORS["ink"], wraplength=750, justify="left").pack(anchor="w")

            selected = tk.IntVar(value=-1)
            self.quiz_answer_vars[question["id"]] = selected

            for opt_idx, option in enumerate(question.get("options", [])):
                tk.Radiobutton(
                    card, text=option.get("option_text", ""), variable=selected, value=opt_idx,
                    font=(FONT, 10), bg=COLORS["surface"], fg=COLORS["ink"],
                    activebackground=COLORS["surface"], wraplength=700, justify="left"
                ).pack(anchor="w", pady=2)

        tk.Button(
            self.content, text="Submit answers", font=(FONT, 10, "bold"),
            bg=COLORS["violet"], fg="white", relief="flat", padx=20, pady=10,
            cursor="hand2", command=self._submit_quiz
        ).pack(anchor="w", pady=16)

    def _submit_quiz(self):
        quiz = self.active_quiz
        if not quiz:
            return

        answers = []
        for question in quiz["questions"]:
            selected_index = self.quiz_answer_vars[question["id"]].get()
            if selected_index < 0:
                messagebox.showwarning(
                    "Incomplete quiz",
                    "Please answer every question before submitting."
                )
                return

            selected_option = question["options"][selected_index]
            answers.append({
                "question_id": question["id"],
                "selected_option_id": selected_option["id"],
            })

        try:
            submission = api_client.submit_attempt(quiz["id"], answers, self.access_token)
            attempt = submission.get("attempt", {})

            result_response = api_client.get_attempt_results(attempt["id"], self.access_token)
            results = result_response.get("attempt", {})

            # Fetch full quiz with option_explanation and is_correct for the review screen
            try:
                full_quiz_resp = api_client.get_quiz(quiz["id"], self.access_token)
                review_quiz = full_quiz_resp.get("quiz", full_quiz_resp) or quiz
            except api_client.APIError:
                review_quiz = quiz  # fallback to take-mode quiz if full fetch fails

            self._show_quiz_results(review_quiz, results)

        except api_client.APIError as exc:
            messagebox.showerror("Submission failed", str(exc))

    def _show_quiz_results(self, quiz, results):
        for widget in self.content.winfo_children():
            widget.destroy()

        score = results.get("score", 0)
        total = results.get("total_questions", len(quiz.get("questions", [])))
        percentage = results.get("accuracy_percentage", 0)

        tk.Label(
            self.content, text="Quiz complete!", font=(FONT, 27, "bold"),
            bg=COLORS["background"], fg=COLORS["ink"]
        ).pack(anchor="w", pady=(12, 3))

        tk.Label(
            self.content,
            text=f"You scored {score} out of {total} ({percentage}%).",
            font=(FONT, 15, "bold"), bg=COLORS["background"], fg=COLORS["violet"]
        ).pack(anchor="w", pady=(0, 12))

        # Render question review cards
        for idx, answer in enumerate(results.get("answers", [])):
            card = tk.Frame(
                self.content, bg=COLORS["surface"], padx=16, pady=12,
                highlightbackground=COLORS["border"], highlightthickness=1
            )
            card.pack(fill="x", pady=5)

            tk.Label(
                card, text=f'{idx + 1}. {answer.get("question_prompt", "Question")}',
                font=(FONT, 10, "bold"), bg=COLORS["surface"], fg=COLORS["ink"],
                wraplength=760, justify="left"
            ).pack(anchor="w")

            selected_text = answer.get("selected_option_text") or "Not answered"
            correct = answer.get("correct_option") or {}
            correct_text = correct.get("option_text", "Unavailable")
            is_correct = answer.get("is_correct", False)

            tk.Label(
                card,
                text=f"Your answer: {selected_text}  ({'✓ Correct' if is_correct else '✗ Incorrect'})",
                font=(FONT, 9, "bold" if is_correct else "normal"),
                bg=COLORS["surface"],
                fg=COLORS["green_text"] if is_correct else COLORS["red_text"],
                wraplength=760, justify="left"
            ).pack(anchor="w", pady=(5, 0))

            if not is_correct:
                tk.Label(
                    card, text=f"Correct answer: {correct_text}",
                    font=(FONT, 9), bg=COLORS["surface"],
                    fg=COLORS["green_text"], wraplength=760, justify="left"
                ).pack(anchor="w", pady=(3, 0))

            # Show all options with their individual explanations
            # Need to find the options from the quiz data
            q_data = next((q for q in quiz.get("questions", []) if q.get("id") == answer.get("question_id")), None)
            if q_data:
                opts = q_data.get("options", [])
                if opts:
                    opts_frame = tk.Frame(card, bg=COLORS["surface"])
                    opts_frame.pack(anchor="w", fill="x", pady=(6, 2))
                    for opt in opts:
                        opt_text = opt.get("option_text", "")
                        opt_is_correct = opt.get("is_correct", False)
                        opt_explanation = opt.get("option_explanation") or ""
                        selected_this = (opt.get("id") == answer.get("selected_option_id"))

                        # Determine color based on correctness and selection
                        if opt_is_correct:
                            opt_color = COLORS["green_text"]
                            prefix_sym = "✓ "
                        elif selected_this:
                            opt_color = COLORS["red_text"]
                            prefix_sym = "✗ "
                        else:
                            opt_color = COLORS["muted"]
                            prefix_sym = "  "

                        opt_label = f"{prefix_sym}{opt_text}"
                        tk.Label(
                            opts_frame, text=opt_label, font=(FONT, 9, "bold" if opt_is_correct else "normal"),
                            bg=COLORS["surface"], fg=opt_color, wraplength=740, justify="left"
                        ).pack(anchor="w", pady=(2, 0))

                        if opt_explanation:
                            tk.Label(
                                opts_frame, text=f"     → {opt_explanation}",
                                font=(FONT, 8, "italic"), bg=COLORS["surface"],
                                fg=COLORS["muted"], wraplength=720, justify="left"
                            ).pack(anchor="w", pady=(0, 2))

            # Overall question explanation
            explanation = answer.get("explanation")
            if explanation:
                tk.Label(
                    card, text=f"Explanation: {explanation}",
                    font=(FONT, 9, "italic"), bg=COLORS["surface"],
                    fg=COLORS["muted"], wraplength=760, justify="left"
                ).pack(anchor="w", pady=(3, 0))

        btn_row = tk.Frame(self.content, bg=COLORS["background"])
        btn_row.pack(anchor="w", pady=16)

        tk.Button(
            btn_row, text="← Back to Explore Quizzes", font=(FONT, 10, "bold"),
            bg=COLORS["violet"], fg="white", relief="flat", padx=16, pady=9,
            cursor="hand2", command=lambda: self.show_page("Explore Quizzes")
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_row, text="View Progress Dashboard", font=(FONT, 10),
            bg=COLORS["surface"], fg=COLORS["ink"], relief="flat", padx=14, pady=9,
            cursor="hand2", command=lambda: self.show_page("Progress")
        ).pack(side="left")

    # -------------------------------------------------------------------------
    # Progress Analytics View
    # -------------------------------------------------------------------------

    def _build_progress(self):
        if not self._require_login("view your progress"):
            return

        tk.Label(self.content, text="Your progress", font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(18, 5))

        try:
            response = api_client.get_progress(self.access_token)
            progress = response.get("progress", {})
        except api_client.APIError as exc:
            messagebox.showerror("Could not load progress", str(exc))
            return

        total_attempts = progress.get("total_attempts", 0)
        total_questions = progress.get("total_questions_answered", 0)
        total_correct = progress.get("total_correct_answers", 0)
        accuracy = progress.get("overall_accuracy_percentage", 0.0)
        recent_attempts = progress.get("recent_attempts", [])

        if total_attempts == 0:
            tk.Label(
                self.content,
                text="Your quiz attempts will appear here after you complete a quiz.",
                font=(FONT, 11), bg=COLORS["background"], fg=COLORS["muted"]
            ).pack(anchor="w", pady=12)

            tk.Button(
                self.content, text="Take a Quiz Now", font=(FONT, 10, "bold"),
                bg=COLORS["violet"], fg="white", relief="flat", padx=16, pady=8,
                command=lambda: self.show_page("Explore Quizzes")
            ).pack(anchor="w")
            return

        summary = tk.Frame(
            self.content, bg=COLORS["surface"], padx=20, pady=18,
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        summary.pack(fill="x", pady=12)

        stats_row = tk.Frame(summary, bg=COLORS["surface"])
        stats_row.pack(fill="x")

        for metric_title, metric_val in [
            ("Total Attempts", str(total_attempts)),
            ("Questions Answered", str(total_questions)),
            ("Correct Answers", str(total_correct)),
            ("Overall Accuracy", f"{accuracy}%"),
        ]:
            col = tk.Frame(stats_row, bg=COLORS["surface"])
            col.pack(side="left", expand=True)
            tk.Label(col, text=metric_val, font=(FONT, 18, "bold"),
                     bg=COLORS["surface"], fg=COLORS["violet"]).pack(anchor="center")
            tk.Label(col, text=metric_title, font=(FONT, 9),
                     bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor="center")

        tk.Label(self.content, text="Recent attempts", font=(FONT, 13, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(16, 6))

        for item in recent_attempts:
            card = tk.Frame(
                self.content, bg=COLORS["surface"], padx=16, pady=10,
                highlightbackground=COLORS["border"], highlightthickness=1
            )
            card.pack(fill="x", pady=4)

            tk.Label(
                card, text=item.get("quiz_title", "Quiz"), font=(FONT, 11, "bold"),
                bg=COLORS["surface"], fg=COLORS["ink"]
            ).pack(side="left")

            details = f"{item.get('score', 0)}/{item.get('total_questions', 0)} ({item.get('accuracy_percentage', 0)}%)  ·  {item.get('submitted_at', '')[:10]}"
            tk.Label(
                card, text=details, font=(FONT, 9),
                bg=COLORS["surface"], fg=COLORS["muted"]
            ).pack(side="right")

    # -------------------------------------------------------------------------
    # Ask Your PDF View (Document Upload + Chat Interface with RAG Boundary)
    # -------------------------------------------------------------------------

    def _build_ask_your_pdf(self):
        if not self._require_login("use Ask Your PDF"):
            return

        header = tk.Frame(self.content, bg=COLORS["background"])
        header.pack(fill="x", pady=(14, 8))
        tk.Label(header, text="Ask Your PDF", font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(side="left")

        # Two-column layout: Left = Documents, Right = Chat
        split_frame = tk.Frame(self.content, bg=COLORS["background"])
        split_frame.pack(fill="both", expand=True)

        left_col = tk.Frame(split_frame, bg=COLORS["background"], width=380)
        left_col.pack(side="left", fill="both", padx=(0, 15))
        left_col.pack_propagate(False)

        right_col = tk.Frame(split_frame, bg=COLORS["surface"],
                             highlightbackground=COLORS["border"], highlightthickness=1)
        right_col.pack(side="left", fill="both", expand=True)

        # Upload Card in Left Column
        upload_card = tk.Frame(left_col, bg=COLORS["surface"], padx=14, pady=12,
                               highlightbackground=COLORS["border"], highlightthickness=1)
        upload_card.pack(fill="x", pady=(0, 10))

        tk.Label(upload_card, text="Upload Study Material (PDF)", font=(FONT, 10, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w")

        selected_file_var = tk.StringVar(value="No file selected")
        tk.Label(upload_card, textvariable=selected_file_var, font=(FONT, 8),
                 bg=COLORS["surface"], fg=COLORS["muted"], wraplength=340).pack(anchor="w", pady=4)

        chosen_path = [None]

        def choose_file():
            path = filedialog.askopenfilename(
                title="Select PDF",
                filetypes=[("PDF files", "*.pdf")]
            )
            if path:
                chosen_path[0] = path
                selected_file_var.set(os.path.basename(path))

        def upload():
            if not chosen_path[0]:
                messagebox.showwarning("No file", "Please select a PDF file to upload.")
                return
            try:
                doc = api_client.upload_document(chosen_path[0], self.access_token)
                messagebox.showinfo("Uploaded", f"PDF processed! Extracted {doc.get('document', {}).get('page_count', 0)} page(s).")
                selected_file_var.set("No file selected")
                chosen_path[0] = None
                load_docs()
            except api_client.APIError as exc:
                messagebox.showerror("Upload failed", str(exc))

        btn_row = tk.Frame(upload_card, bg=COLORS["surface"])
        btn_row.pack(fill="x", pady=(6, 0))
        tk.Button(btn_row, text="Browse...", font=(FONT, 9), relief="solid", bd=1,
                  bg="#FFFFFF", command=choose_file, cursor="hand2").pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="Upload & Process", font=(FONT, 9, "bold"), bg=COLORS["violet"],
                  fg="white", relief="flat", command=upload, cursor="hand2").pack(side="left")

        # Documents list
        tk.Label(left_col, text="Your Documents", font=(FONT, 11, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(8, 4))
        docs_list_frame = tk.Frame(left_col, bg=COLORS["background"])
        docs_list_frame.pack(fill="both", expand=True)

        def load_docs():
            for w in docs_list_frame.winfo_children():
                w.destroy()
            try:
                res = api_client.get_documents(self.access_token)
                documents = res.get("documents", [])
            except api_client.APIError:
                documents = []

            if not documents:
                tk.Label(docs_list_frame, text="No PDFs uploaded yet.", font=(FONT, 9),
                         bg=COLORS["background"], fg=COLORS["muted"]).pack(anchor="w", pady=4)
                return

            for doc in documents:
                d_card = tk.Frame(docs_list_frame, bg=COLORS["surface"], padx=10, pady=8,
                                  highlightbackground=COLORS["border"], highlightthickness=1)
                d_card.pack(fill="x", pady=3)

                name = doc.get("original_filename", "Document.pdf")
                pages = doc.get("page_count", 0)
                tk.Label(d_card, text=name, font=(FONT, 9, "bold"),
                         bg=COLORS["surface"], fg=COLORS["ink"], wraplength=220, justify="left").pack(anchor="w")
                tk.Label(d_card, text=f"{pages} page(s)", font=(FONT, 8),
                         bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor="w")

                actions = tk.Frame(d_card, bg=COLORS["surface"])
                actions.pack(fill="x", pady=(4, 0))

                tk.Button(
                    actions, text="Chat 💬", font=(FONT, 8, "bold"), bg=COLORS["violet_light"],
                    fg=COLORS["ink"], relief="flat", cursor="hand2",
                    command=lambda did=doc["id"], title=name: start_session(did, title)
                ).pack(side="left", padx=(0, 6))

                tk.Button(
                    actions, text="Delete", font=(FONT, 8), bg=COLORS["surface"],
                    fg=COLORS["red_text"], relief="flat", cursor="hand2",
                    command=lambda did=doc["id"]: delete_doc(did)
                ).pack(side="left")

        def delete_doc(doc_id):
            if messagebox.askyesno("Delete Document", "Delete this PDF document?"):
                try:
                    api_client.delete_document(doc_id, self.access_token)
                    load_docs()
                except api_client.APIError as exc:
                    messagebox.showerror("Error", str(exc))

        # Right Column: Chat Window
        chat_header = tk.Frame(right_col, bg=COLORS["surface"], padx=16, pady=12)
        chat_header.pack(fill="x")
        chat_title_var = tk.StringVar(value="Select a document on the left to start studying")
        tk.Label(chat_header, textvariable=chat_title_var, font=(FONT, 12, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w")

        chat_messages_frame = tk.Frame(right_col, bg=COLORS["background"], padx=14, pady=10)
        chat_messages_frame.pack(fill="both", expand=True)

        query_frame = tk.Frame(right_col, bg=COLORS["surface"], padx=14, pady=10)
        query_frame.pack(fill="x", side="bottom")

        query_var = tk.StringVar()
        query_entry = tk.Entry(query_frame, textvariable=query_var, font=(FONT, 10),
                               relief="solid", bd=1)
        query_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))

        def start_session(doc_id, doc_title):
            try:
                res = api_client.create_chat_session(doc_id, self.access_token, title=f"Study: {doc_title}")
                session = res.get("session", {})
                self.active_chat_session = session
                chat_title_var.set(f"💬 {session.get('title', doc_title)}")
                refresh_messages()
            except api_client.APIError as exc:
                messagebox.showerror("Could not start session", str(exc))

        def refresh_messages():
            for w in chat_messages_frame.winfo_children():
                w.destroy()
            if not self.active_chat_session:
                return

            try:
                res = api_client.get_chat_messages(self.active_chat_session["id"], self.access_token)
                messages = res.get("messages", [])
            except api_client.APIError:
                messages = []

            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                bubble = tk.Frame(
                    chat_messages_frame,
                    bg=COLORS["violet_light"] if role == "user" else COLORS["surface"],
                    padx=12, pady=8,
                    highlightbackground=COLORS["border"], highlightthickness=1
                )
                bubble.pack(anchor="e" if role == "user" else "w", pady=4, fill="x")
                prefix = "You: " if role == "user" else "FORMA AI: "
                tk.Label(
                    bubble, text=prefix + content, font=(FONT, 9),
                    bg=COLORS["violet_light"] if role == "user" else COLORS["surface"],
                    fg=COLORS["ink"], wraplength=450, justify="left"
                ).pack(anchor="w")

        def send_query():
            q = query_var.get().strip()
            if not q:
                return
            if not self.active_chat_session:
                messagebox.showwarning("No active session", "Please click 'Chat' on a document first.")
                return

            query_var.set("")

            # User query bubble immediately displayed
            user_bubble = tk.Frame(
                chat_messages_frame, bg=COLORS["violet_light"], padx=12, pady=8,
                highlightbackground=COLORS["border"], highlightthickness=1
            )
            user_bubble.pack(anchor="e", pady=4, fill="x")
            tk.Label(user_bubble, text="You: " + q, font=(FONT, 9),
                     bg=COLORS["violet_light"], fg=COLORS["ink"], wraplength=450, justify="left").pack(anchor="w")

            try:
                result = api_client.send_chat_message(self.active_chat_session["id"], q, self.access_token)
                # Show AI response in the chat
                ai_resp = result.get("assistant_message", {})
                ai_content = ai_resp.get("content", "")
                citations = ai_resp.get("citations") or []

                ai_bubble = tk.Frame(
                    chat_messages_frame, bg=COLORS["surface"], padx=12, pady=8,
                    highlightbackground=COLORS["border"], highlightthickness=1
                )
                ai_bubble.pack(anchor="w", pady=4, fill="x")
                tk.Label(
                    ai_bubble, text="FORMA AI: " + ai_content, font=(FONT, 9),
                    bg=COLORS["surface"], fg=COLORS["ink"], wraplength=450, justify="left"
                ).pack(anchor="w")
                if citations:
                    pages_cited = ", ".join(f"p.{c['page_number']}" for c in citations)
                    tk.Label(
                        ai_bubble, text=f"📄 Sources: {pages_cited}",
                        font=(FONT, 8, "italic"), bg=COLORS["surface"],
                        fg=COLORS["muted"], wraplength=450, justify="left"
                    ).pack(anchor="w", pady=(2, 0))

            except api_client.RAGNotImplementedError:
                # Only shown if the server has no API key configured
                rag_bubble = tk.Frame(
                    chat_messages_frame, bg=COLORS["butter"], padx=12, pady=10,
                    highlightbackground=COLORS["border"], highlightthickness=1
                )
                rag_bubble.pack(anchor="w", pady=6, fill="x")
                tk.Label(
                    rag_bubble,
                    text="⚠️  The AI backend is not configured on the server. Please set OPENAI_API_KEY in backend/.env and restart.",
                    font=(FONT, 9, "bold"), bg=COLORS["butter"], fg=COLORS["orange_text"],
                    wraplength=450, justify="left"
                ).pack(anchor="w")

            except api_client.APIError as exc:
                messagebox.showerror("Chat error", str(exc))

        tk.Button(
            query_frame, text="Send ➔", font=(FONT, 10, "bold"), bg=COLORS["violet"],
            fg="white", relief="flat", padx=16, pady=6, cursor="hand2", command=send_query
        ).pack(side="left")

        # Initial load of documents
        load_docs()

    # -------------------------------------------------------------------------
    # Settings & Configuration View
    # -------------------------------------------------------------------------

    def _build_settings(self):
        tk.Label(self.content, text="Settings & Status", font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(20, 6))

        card = tk.Frame(
            self.content, bg=COLORS["surface"], padx=22, pady=20,
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        card.pack(fill="x", anchor="nw")

        tk.Label(card, text="Backend API Configuration", font=(FONT, 13, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w", pady=(0, 8))

        url_var = tk.StringVar(value=api_client.get_base_url())
        self._simple_field(card, "API Base URL", url_var)

        status_lbl = tk.Label(card, text="Checking connection...", font=(FONT, 9),
                              bg=COLORS["surface"], fg=COLORS["muted"])
        status_lbl.pack(anchor="w", pady=(8, 12))

        def test_conn():
            url = url_var.get().strip()
            api_client.set_base_url(url)
            try:
                res = api_client.request("GET", "/health/ready")
                status_lbl.configure(
                    text=f"✓ Connected to FORMA backend ({res.get('database', 'ready')})",
                    fg=COLORS["green_text"]
                )
                messagebox.showinfo("Connection Successful", f"Successfully reached {url}")
            except api_client.APIError as exc:
                status_lbl.configure(text=f"✗ Offline: {str(exc)}", fg=COLORS["red_text"])
                messagebox.showerror("Connection Error", str(exc))

        btn_row = tk.Frame(card, bg=COLORS["surface"])
        btn_row.pack(anchor="w")

        tk.Button(
            btn_row, text="Test Connection", font=(FONT, 9, "bold"),
            bg=COLORS["violet"], fg="white", relief="flat", padx=14, pady=8,
            cursor="hand2", command=test_conn
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_row, text="Reset to Default", font=(FONT, 9),
            bg=COLORS["surface"], fg=COLORS["ink"], relief="solid", bd=1, padx=12, pady=8,
            cursor="hand2", command=lambda: url_var.set("http://127.0.0.1:5000/api/v1")
        ).pack(side="left")

        # Test initial connectivity on screen load
        test_conn()

    def _build_placeholder(self, page):
        tk.Label(self.content, text=page, font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(25, 5))
        tk.Label(self.content, text="This screen is part of the FORMA plan. We'll build it next.",
                 font=(FONT, 11), bg=COLORS["background"], fg=COLORS["muted"]).pack(anchor="w")


if __name__ == "__main__":
    app = FormaApp()
    app.mainloop()
