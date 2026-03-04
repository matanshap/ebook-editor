#!/usr/bin/env python3
"""Desktop GUI for ebook-editor.

Uses Tkinter so it works out-of-the-box on Windows Python installs and keeps
interface concerns separate from processing logic for future feature growth.
"""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ebook_editor_core import BuildRequest, build_bilingual_pdf


class EbookEditorGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ebook-editor | Bilingual PDF Builder")
        self.root.geometry("760x520")

        self.left_var = tk.StringVar()
        self.right_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.left_label_var = tk.StringVar(value="L1")
        self.right_label_var = tk.StringVar(value="L2")
        self.font_var = tk.StringVar()

        self._build_layout()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(
            container,
            text="Bilingual PDF Builder",
            font=("Segoe UI", 14, "bold"),
        )
        title.pack(anchor="w", pady=(0, 8))

        hint = ttk.Label(
            container,
            text=(
                "Choose source PDFs, configure labels/font, then click Build. "
                "Core logic is modular so more workflows can be added later "
                "without replacing this UI."
            ),
            wraplength=710,
        )
        hint.pack(anchor="w", pady=(0, 12))

        form = ttk.Frame(container)
        form.pack(fill=tk.X)

        self._add_file_row(form, "Left PDF", self.left_var, self._choose_left)
        self._add_file_row(form, "Right PDF", self.right_var, self._choose_right)
        self._add_file_row(form, "Output PDF", self.output_var, self._choose_output, save=True)
        self._add_file_row(form, "Font (optional)", self.font_var, self._choose_font)

        labels_row = ttk.Frame(form)
        labels_row.pack(fill=tk.X, pady=6)
        ttk.Label(labels_row, text="Left label", width=14).pack(side=tk.LEFT)
        ttk.Entry(labels_row, textvariable=self.left_label_var, width=12).pack(side=tk.LEFT, padx=(0, 18))
        ttk.Label(labels_row, text="Right label", width=14).pack(side=tk.LEFT)
        ttk.Entry(labels_row, textvariable=self.right_label_var, width=12).pack(side=tk.LEFT)

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=10)
        self.build_button = ttk.Button(actions, text="Build PDF", command=self._run_build)
        self.build_button.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(actions, textvariable=self.status_var).pack(side=tk.LEFT, padx=12)

        self.log_box = tk.Text(container, height=15, wrap=tk.WORD)
        self.log_box.pack(fill=tk.BOTH, expand=True)
        self.log_box.insert(tk.END, "Welcome. Configure files and click Build PDF.\n")
        self.log_box.configure(state=tk.DISABLED)

    def _add_file_row(self, parent: ttk.Frame, label: str, var: tk.StringVar, command, save: bool = False) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text=label, width=14).pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(row, text="Browse", command=command).pack(side=tk.LEFT)

    def _choose_left(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if path:
            self.left_var.set(path)

    def _choose_right(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if path:
            self.right_var.set(path)

    def _choose_output(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if path:
            self.output_var.set(path)

    def _choose_font(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("TrueType font", "*.ttf"), ("All files", "*.*")])
        if path:
            self.font_var.set(path)

    def _append_log(self, line: str) -> None:
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, f"{line}\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state=tk.DISABLED)

    def _run_build(self) -> None:
        left = Path(self.left_var.get()).expanduser()
        right = Path(self.right_var.get()).expanduser()
        output = Path(self.output_var.get()).expanduser()
        font_text = self.font_var.get().strip()
        font = Path(font_text).expanduser() if font_text else None

        if not left.exists() or not right.exists():
            messagebox.showerror("Missing input", "Please provide valid left/right PDF files.")
            return
        if font and not font.exists():
            messagebox.showerror("Missing font", "The selected font file was not found.")
            return
        if not output.parent.exists():
            messagebox.showerror("Invalid output", "The output directory does not exist.")
            return

        request = BuildRequest(
            left_pdf=left,
            right_pdf=right,
            output_pdf=output,
            left_label=self.left_label_var.get().strip() or "L1",
            right_label=self.right_label_var.get().strip() or "L2",
            font_path=font,
        )

        self.build_button.configure(state=tk.DISABLED)
        self.status_var.set("Building...")
        self._append_log("Starting build...")

        def worker() -> None:
            try:
                result = build_bilingual_pdf(request, progress=lambda msg: self.root.after(0, self._append_log, msg))
                self.root.after(0, self._on_success, result)
            except Exception as exc:  # broad for GUI error reporting
                self.root.after(0, self._on_error, exc)

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, result) -> None:
        self.build_button.configure(state=tk.NORMAL)
        self.status_var.set("Finished")
        self._append_log(
            f"Output written to {result.output_pdf} | pairs={result.pair_count} "
            f"left={result.left_sentence_count} right={result.right_sentence_count}"
        )
        messagebox.showinfo("Success", f"Created {result.output_pdf}")

    def _on_error(self, exc: Exception) -> None:
        self.build_button.configure(state=tk.NORMAL)
        self.status_var.set("Failed")
        self._append_log(f"Error: {exc}")
        messagebox.showerror("Build failed", str(exc))


def main() -> None:
    root = tk.Tk()
    EbookEditorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
