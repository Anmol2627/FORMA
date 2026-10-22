import tkinter as tk
from tkinter import messagebox
import re

from .config import APP_NAME, WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT
from .theme import COLORS, FONT
from .services import database
from .services import api_client

class FormaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.configure(bg=COLORS["background"])

        # Local SQLite prototype storage persists accounts, quizzes and attempts across restarts.
        # This can later be replaced by the real backend API.
        database.initialize_database()
        self.current_user = None
        self.access_token = None
        self.active_quiz = None
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
        tk.Label(brand, text="✿", font=(FONT, 24, "bold"), fg=COLORS["violet"],
                 bg=COLORS["sidebar"]).pack(side="left", padx=(0, 9))
        tk.Label(brand, text=APP_NAME, font=(FONT, 19, "bold"), fg=COLORS["ink"],
                 bg=COLORS["sidebar"]).pack(side="left")

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
        tk.Label(self.sidebar, text="🐾  Small steps\n     Big progress", justify="left",
                 font=(FONT, 10, "italic"), fg=COLORS["muted"],
                 bg=COLORS["sidebar"]).pack(padx=22, pady=18, anchor="w")
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
        tk.Label(self.topbar, text="♧", font=(FONT, 17), bg=COLORS["background"],
                 fg=COLORS["ink"]).pack(side="left", padx=12)
        self.profile_button = tk.Button(
            self.topbar, text="◉  Sign in / Sign up  ⌄", font=(FONT, 10, "bold"),
            relief="flat", bd=0, cursor="hand2", bg=COLORS["background"],
            fg=COLORS["ink"], activebackground=COLORS["violet_light"],
            command=self.toggle_profile_menu
        )
        self.profile_button.pack(side="left", padx=(5, 0))
        self.profile_menu = tk.Frame(self.main, bg=COLORS["surface"],
                                     highlightbackground=COLORS["border"], highlightthickness=1)

        self.content = tk.Frame(self.main, bg=COLORS["background"])
        self.content.pack(fill="both", expand=True, padx=30, pady=(0, 12))
        self._update_profile_button()

    def _update_profile_button(self):
        if self.current_user:
            display = self.current_user["display_name"]
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

        if page == "Explore Quizzes":
            self._build_explore()
        elif page == "Create Quiz":
            self._build_create_quiz()
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
        else:
            self._build_placeholder(page)

    def _build_auth(self, mode):
        panel = tk.Frame(self.content, bg=COLORS["background"])
        panel.pack(fill="both", expand=True, anchor="n")
        # Let the card size itself to fit all fields and buttons. Disabling geometry
        # propagation here without setting a height collapsed the card and clipped
        # the authentication controls on some Tk builds.
        card = tk.Frame(panel, bg=COLORS["surface"], highlightbackground=COLORS["border"],
                        highlightthickness=1, padx=34, pady=28, width=430)
        card.pack(anchor="n", pady=30)

        tk.Label(card, text="✿  FORMA", font=(FONT, 13, "bold"),
                 bg=COLORS["surface"], fg=COLORS["violet"]).pack(anchor="w")
        tk.Label(card, text=mode, font=(FONT, 25, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w", pady=(16, 4))
        subtitle = "Welcome back! Sign in to continue learning." if mode == "Sign in" else "Create an account and make every step count."
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
                messagebox.showwarning(
                    "Missing details",
                    "Please enter your email and password."
                )
                return

            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                messagebox.showwarning(
                    "Invalid email",
                    "Enter a valid email address."
                )
                return

            if len(password) < 8:
                messagebox.showwarning(
                    "Password too short",
                    "Use at least 8 characters."
                )
                return

            if mode == "Sign up":
                if not display_name:
                    messagebox.showwarning(
                        "Missing name",
                        "Please enter a display name."
                    )
                    return

                if password != confirm_var.get():
                    messagebox.showwarning(
                        "Passwords don't match",
                        "Please make sure both passwords match."
                    )
                    return

            try:
                if mode == "Sign up":
                    response = api_client.register(
                        display_name, email, password
                    )
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

                messagebox.showinfo(
                    "Success",
                    f"Welcome, {user['display_name']}!"
                )
                self.show_page("Explore Quizzes")

            except api_client.APIError as exc:
                messagebox.showerror(
                    "Authentication failed",
                    str(exc)
                )
            except (KeyError, TypeError, ValueError):
                messagebox.showerror(
                    "Unexpected response",
                    "The backend returned an unexpected response. Please try again."
                )

        # Primary action: submit the sign-in or sign-up form.
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

        # Let users switch between account creation and sign-in.
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
            text="Your account is handled by FORMA's backend",
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
        card = tk.Frame(self.content, bg=COLORS["surface"], padx=24, pady=22,
                        highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(anchor="nw", fill="x")
        tk.Label(card, text=self.current_user["display_name"], font=(FONT, 17, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w")
        tk.Label(card, text=self.current_user["email"], font=(FONT, 10),
                 bg=COLORS["surface"], fg=COLORS["muted"]).pack(anchor="w", pady=(4, 16))
        tk.Button(card, text="Log out", font=(FONT, 10, "bold"), bg=COLORS["violet"],
                  fg="white", relief="flat", padx=16, pady=8,
                  command=self.logout).pack(anchor="w")

    def logout(self):
        self.current_user = None
        self.access_token = None
        self._update_profile_button()
        self.show_page("Explore Quizzes")
        messagebox.showinfo("Signed out", "You have been signed out.")

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
            tk.Button(filters, text=label, font=(FONT, 9), relief="flat", bd=0,
                      padx=13, pady=7, cursor="hand2",
                      bg=COLORS["violet"] if active else COLORS["surface"],
                      fg="white" if active else COLORS["ink"],
                      activebackground=COLORS["violet_light"],
                      command=lambda value=label: self._filter_notice(value)).pack(side="left", padx=(0, 7))

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
            card = tk.Frame(cards_area, bg=COLORS["surface"], highlightbackground=COLORS["border"],
                            highlightthickness=1, padx=15, pady=11)
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
            tk.Button(bottom, text="→", font=(FONT, 11, "bold"), relief="flat", bd=0,
                      bg=COLORS["surface"], fg=COLORS["ink"], cursor="hand2",
                      command=lambda subject=title: self._open_subject(subject)).pack(side="right")
        footer = tk.Frame(self.content, bg="#F2F1F7", padx=12, pady=8)
        footer.pack(fill="x", pady=(7, 0))
        tk.Label(footer, text="✦", font=(FONT, 14), fg=COLORS["violet"],
                 bg="#F2F1F7").pack(side="left", padx=(0, 15))
        tk.Label(footer, text="Find the right quiz for your next step.",
                 font=(FONT, 9), fg=COLORS["muted"], bg="#F2F1F7").pack(side="left")

    def _filter_notice(self, subject):
        if subject == "All":
            self.show_page("Explore Quizzes")
        else:
            self._open_subject(subject)
            
    def _open_subject(self, subject):
        if not self.access_token:
            messagebox.showinfo(
                "Sign in required",
                "Please sign in to view available quizzes."
            )
            self.show_page("Sign in")
            return

        for widget in self.content.winfo_children():
            widget.destroy()

        tk.Label(
            self.content,
            text=subject,
            font=(FONT, 25, "bold"),
            bg=COLORS["background"],
            fg=COLORS["ink"]
        ).pack(anchor="w", pady=(14, 4))

        tk.Button(
            self.content,
            text="← Back to Explore",
            command=lambda: self.show_page("Explore Quizzes")
        ).pack(anchor="w", pady=8)

        try:
            response = api_client.get_quizzes(self.access_token)
            quizzes = response.get("quizzes", [])
        except api_client.APIError as exc:
            messagebox.showerror("Could not load quizzes", str(exc))
            return

        if not quizzes:
            tk.Label(
                self.content,
                text="No quizzes found. Create a quiz first or try again later.",
                font=(FONT, 11),
                bg=COLORS["background"],
                fg=COLORS["muted"]
            ).pack(anchor="w", pady=16)
            return

        for quiz in quizzes:
            card = tk.Frame(
                self.content,
                bg=COLORS["surface"],
                padx=16,
                pady=12
            )
            card.pack(fill="x", pady=6)

            tk.Label(
                card,
                text=quiz.get("title", "Untitled quiz"),
                font=(FONT, 13, "bold"),
                bg=COLORS["surface"],
                fg=COLORS["ink"]
            ).pack(anchor="w")

            tk.Label(
                card,
                text=(
                    f'{quiz.get("description") or "Ready to practise"}'
                    f' · {quiz.get("question_count", 0)} questions'
                ),
                font=(FONT, 10),
                bg=COLORS["surface"],
                fg=COLORS["muted"],
                wraplength=700
            ).pack(anchor="w", pady=5)

            tk.Button(
                card,
                text="Take quiz →",
                command=lambda qid=quiz["id"]: self._start_quiz(qid)
            ).pack(anchor="w", pady=5)

    def _start_quiz(self, quiz_id):
        if not self.access_token:
            messagebox.showinfo(
                "Sign in required",
                "Please sign in first."
            )
            self.show_page("Sign in")
            return

        try:
            response = api_client.get_quiz_to_take(
                quiz_id, self.access_token
            )
            self.active_quiz = response["quiz"]
            self.quiz_answer_vars = {}
            self.show_page("Take Quiz")
        except api_client.APIError as exc:
            messagebox.showerror("Could not open quiz", str(exc))
        except (KeyError, TypeError):
            messagebox.showerror(
                "Invalid response",
                "The backend returned unexpected quiz data."
            )

    def _require_login(self, action_name):
        if self.current_user:
            return True
        messagebox.showinfo("Sign in required", f"Please sign in or create an account to {action_name}.")
        self.show_page("Sign in")
        return False

    def _build_create_quiz(self):
        if not self._require_login("create a quiz"):
            return
        tk.Label(self.content, text="Create a quiz", font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(16, 4))
        tk.Label(self.content, text="Build a quiz and save it to your local FORMA library.",
                 font=(FONT, 10), bg=COLORS["background"], fg=COLORS["muted"]).pack(anchor="w", pady=(0, 12))

        form = tk.Frame(self.content, bg=COLORS["surface"], padx=18, pady=16,
                        highlightbackground=COLORS["border"], highlightthickness=1)
        form.pack(fill="x", anchor="n")
        title_var, desc_var = tk.StringVar(), tk.StringVar()
        self._simple_field(form, "Quiz title", title_var)
        self._simple_field(form, "Description (optional)", desc_var)

        question_frame = tk.Frame(form, bg=COLORS["surface"])
        question_frame.pack(fill="x", pady=(10, 0))
        tk.Label(question_frame, text="Question 1", font=(FONT, 12, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w")
        prompt_var = tk.StringVar()
        self._simple_field(question_frame, "Question prompt", prompt_var)
        option_vars = [tk.StringVar() for _ in range(4)]
        correct_var = tk.IntVar(value=0)
        tk.Label(question_frame, text="Answer options (select the correct answer)",
                 font=(FONT, 9, "bold"), bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w", pady=(8, 4))
        for i, var in enumerate(option_vars):
            line = tk.Frame(question_frame, bg=COLORS["surface"])
            line.pack(fill="x", pady=3)
            tk.Radiobutton(line, variable=correct_var, value=i, bg=COLORS["surface"],
                           activebackground=COLORS["surface"]).pack(side="left")
            tk.Entry(line, textvariable=var, font=(FONT, 10), relief="solid", bd=1,
                     bg="#FFFFFF").pack(side="left", fill="x", expand=True, ipady=5)
        explanation_var = tk.StringVar()
        self._simple_field(question_frame, "Explanation shown after answering (optional)", explanation_var)

        
        def save():
            title = title_var.get().strip()
            prompt = prompt_var.get().strip()
            options = [v.get().strip() for v in option_vars]

            if not title or not prompt or any(not value for value in options):
                messagebox.showwarning(
                    "Missing details",
                    "Enter a quiz title, a question, and all four answer options."
                )
                return

            questions = [{
                "prompt": prompt,
                "explanation": explanation_var.get().strip(),
                "options": [
                    {
                        "option_text": option,
                        "is_correct": index == correct_var.get()
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
                    visibility="public"
                )

                messagebox.showinfo(
                    "Quiz saved",
                    "Your quiz has been saved successfully!"
                )
                self.show_page("My Quizzes")

            except api_client.APIError as exc:
                messagebox.showerror("Could not save quiz", str(exc))
    
        tk.Button(
            form,
            text="Save Quiz",
            font=(FONT, 11, "bold"),
            bg=COLORS["violet"],
            fg="#FFFFFF",
            activebackground=COLORS["violet"],
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=24,
            pady=10,
            cursor="hand2",
            command=save,
        ).pack(anchor="e", pady=(16, 0))

    def _simple_field(self, parent, label, variable):
        tk.Label(parent, text=label, font=(FONT, 9, "bold"),
                 bg=COLORS["surface"], fg=COLORS["ink"]).pack(anchor="w", pady=(7, 4))
        entry = tk.Entry(parent, textvariable=variable, font=(FONT, 10),
                         relief="solid", bd=1, bg="#FFFFFF", fg=COLORS["ink"])
        entry.pack(fill="x", ipady=6)
        return entry

    
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
            padx=14, pady=8,
            command=lambda: self.show_page("Create Quiz")
        ).pack(side="right")

        try:
            response = api_client.request(
                "GET", "/quizzes?include_public=false",
                token=self.access_token
            )
            quizzes = response.get("quizzes", [])
        except api_client.APIError as exc:
            messagebox.showerror("Could not load quizzes", str(exc))
            return

        if not quizzes:
            tk.Label(
                self.content,
                text="Your quiz library is empty for now.",
                font=(FONT, 12),
                bg=COLORS["background"], fg=COLORS["muted"]
            ).pack(anchor="w", pady=20)

            tk.Label(
                self.content,
                text="Create your first quiz to see it here.",
                font=(FONT, 10),
                bg=COLORS["background"], fg=COLORS["muted"]
            ).pack(anchor="w")
            return

        for quiz in quizzes:
            card = tk.Frame(
                self.content, bg=COLORS["surface"], padx=16, pady=13,
                highlightbackground=COLORS["border"],
                highlightthickness=1
            )
            card.pack(fill="x", pady=5)

            info = tk.Frame(card, bg=COLORS["surface"])
            info.pack(side="left", fill="x", expand=True)

            tk.Label(
                info, text=quiz.get("title", "Untitled quiz"),
                font=(FONT, 12, "bold"),
                bg=COLORS["surface"], fg=COLORS["ink"]
            ).pack(anchor="w")

            description = quiz.get("description") or "No description"
            count = quiz.get("question_count", 0)

            tk.Label(
                info, text=f"{count} question(s)  ·  {description}",
                font=(FONT, 9),
                bg=COLORS["surface"], fg=COLORS["muted"]
            ).pack(anchor="w", pady=(4, 0))

            tk.Button(
                card, text="Take quiz  →",
                font=(FONT, 9, "bold"),
                bg=COLORS["violet_light"], fg=COLORS["ink"],
                relief="flat", padx=12, pady=7,
                command=lambda qid=quiz["id"]: self._start_quiz(qid)
            ).pack(side="right")

    def _take_quiz(self, quiz_id):
        if not self._require_login("take a quiz"):
            return
        quiz = database.get_quiz(quiz_id)
        if not quiz or not quiz["questions"]:
            messagebox.showerror("Quiz unavailable", "This quiz could not be loaded.")
            return
        self.active_quiz = quiz
        self.quiz_answer_vars = {}
        self.show_page("Take Quiz")

    def _build_take_quiz(self):
        quiz = self.active_quiz
        if not quiz:
            self._build_placeholder("Take Quiz")
            return
        tk.Label(self.content, text=quiz["title"], font=(FONT, 25, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(14, 4))
        tk.Label(self.content, text="Choose one answer for each question, then submit.",
                 font=(FONT, 10), bg=COLORS["background"], fg=COLORS["muted"]).pack(anchor="w", pady=(0, 12))
        for idx, question in enumerate(quiz["questions"]):
            card = tk.Frame(self.content, bg=COLORS["surface"], padx=16, pady=12,
                            highlightbackground=COLORS["border"], highlightthickness=1)
            card.pack(fill="x", pady=6)
            tk.Label(card, text=f'{idx + 1}. {question["prompt"]}', font=(FONT, 11, "bold"),
                     bg=COLORS["surface"], fg=COLORS["ink"], wraplength=750, justify="left").pack(anchor="w")
            selected = tk.IntVar(value=-1)
            self.quiz_answer_vars[question["id"]] = selected
            for opt_idx, option in enumerate(question["options"]):
                tk.Radiobutton(card, text=option["option_text"], variable=selected, value=opt_idx,
                               font=(FONT, 10), bg=COLORS["surface"], fg=COLORS["ink"],
                               activebackground=COLORS["surface"], wraplength=700,
                               justify="left").pack(anchor="w", pady=2)
        tk.Button(self.content, text="Submit answers", font=(FONT, 10, "bold"),
                  bg=COLORS["violet"], fg="white", relief="flat", padx=18, pady=10,
                  command=self._submit_quiz).pack(anchor="w", pady=12)
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
            submission = api_client.submit_attempt(
                quiz["id"], answers, self.access_token
            )
            attempt = submission["attempt"]

            result_response = api_client.get_attempt_results(
                attempt["id"], self.access_token
            )
            results = result_response["attempt"]

            self._show_quiz_results(quiz, results)

        except api_client.APIError as exc:
            messagebox.showerror("Submission failed", str(exc))
        except (KeyError, TypeError) as exc:
            messagebox.showerror(
                "Invalid response",
                f"The backend returned unexpected result data: {exc}"
            )

    def _show_quiz_results(self, quiz, results):
        for widget in self.content.winfo_children():
            widget.destroy()
    def _show_quiz_results(self, quiz, results):
        for widget in self.content.winfo_children():
            widget.destroy()

        score = results.get("score", 0)
        total = results.get("total_questions", len(quiz["questions"]))
        percentage = results.get("accuracy_percentage", 0)

        tk.Label(
            self.content,
            text="Quiz complete!",
            font=(FONT, 27, "bold"),
            bg=COLORS["background"],
            fg=COLORS["ink"]
        ).pack(anchor="w", pady=(12, 3))

        tk.Label(
            self.content,
            text=f"You scored {score} out of {total} ({percentage}%).",
            font=(FONT, 15, "bold"),
            bg=COLORS["background"],
            fg=COLORS["violet"]
        ).pack(anchor="w", pady=(0, 12))

        for idx, answer in enumerate(results.get("answers", [])):
            card = tk.Frame(
                self.content,
                bg=COLORS["surface"],
                padx=14,
                pady=10,
                highlightbackground=COLORS["border"],
                highlightthickness=1
            )
            card.pack(fill="x", pady=5)
        tk.Label(
            card,
            text=f'{idx + 1}. {answer.get("question_prompt", "Question")}',
            font=(FONT, 10, "bold"), bg=COLORS["surface"],
            fg=COLORS["ink"], wraplength=760, justify="left"
        ).pack(anchor="w")

        selected_text = answer.get("selected_option_text") or "Not answered"
        correct = answer.get("correct_option") or {}
        correct_text = correct.get("option_text", "Unavailable")

        tk.Label(
            card, text=f"Your answer: {selected_text}",
            font=(FONT, 9), bg=COLORS["surface"],
            fg=COLORS["green_text"] if answer.get("is_correct")
            else COLORS["muted"],
            wraplength=760, justify="left"
        ).pack(anchor="w", pady=(5, 0))

        tk.Label(
            card, text=f"Correct answer: {correct_text}",
            font=(FONT, 9), bg=COLORS["surface"],
            fg=COLORS["green_text"], wraplength=760, justify="left"
        ).pack(anchor="w", pady=(3, 0))

        explanation = answer.get("explanation")
        if explanation:
            tk.Label(
                card, text=f"Explanation: {explanation}",
                font=(FONT, 9), bg=COLORS["surface"],
                fg=COLORS["muted"], wraplength=760, justify="left"
            ).pack(anchor="w", pady=(3, 0))

            tk.Button(
            self.content,
            text="Back to Explore Quizzes",
            font=(FONT, 10, "bold"),
            bg=COLORS["violet"],
            fg="white",
            relief="flat",
            padx=16,
            pady=9,
            command=lambda: self.show_page("Explore Quizzes")
        ).pack(anchor="w", pady=12)
    def _build_progress(self):
        if not self._require_login("view your progress"):
            return
        attempts = database.list_attempts(self.current_user["id"])
        tk.Label(self.content, text="Your progress", font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(18, 5))
        if not attempts:
            tk.Label(self.content, text="Your quiz attempts will appear here after you complete a quiz.",
                     font=(FONT, 10), bg=COLORS["background"], fg=COLORS["muted"]).pack(anchor="w", pady=12)
            return
        total_questions = sum(item["total"] for item in attempts)
        total_correct = sum(item["score"] for item in attempts)
        accuracy = round(total_correct / total_questions * 100) if total_questions else 0
        summary = tk.Frame(self.content, bg=COLORS["surface"], padx=18, pady=16,
                           highlightbackground=COLORS["border"], highlightthickness=1)
        summary.pack(fill="x", pady=12)
        tk.Label(summary, text=f"{len(attempts)} attempts     {total_correct}/{total_questions} correct     {accuracy}% accuracy",
                 font=(FONT, 13, "bold"), bg=COLORS["surface"], fg=COLORS["violet"]).pack(anchor="w")
        tk.Label(self.content, text="Recent attempts", font=(FONT, 13, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(8, 4))
        for item in attempts:
            tk.Label(self.content, text=f'{item["title"]}  ·  {item["score"]}/{item["total"]}  ·  {item["created_at"]}',
                     font=(FONT, 10), bg=COLORS["background"], fg=COLORS["muted"]).pack(anchor="w", pady=4)

    def _build_placeholder(self, page):
        tk.Label(self.content, text=page, font=(FONT, 27, "bold"),
                 bg=COLORS["background"], fg=COLORS["ink"]).pack(anchor="w", pady=(25, 5))
        tk.Label(self.content, text="This screen is part of the FORMA plan. We'll build it next.",
                 font=(FONT, 11), bg=COLORS["background"], fg=COLORS["muted"]).pack(anchor="w")
