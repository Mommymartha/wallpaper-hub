import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from . import config
from . import main as controller_main

# --- Global appearance ---------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT_GREEN = "#2FA572"
ACCENT_GREEN_HOVER = "#268F62"
FONT_FAMILY = "Segoe UI"


class ControllerApp:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title("Wallpaper Fleet Controller")
        self.root.geometry("480x400")
        self.root.resizable(False, False)

        self.image_path = tk.StringVar()

        # --- Header -------------------------------------------------
        header = ctk.CTkFrame(root, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(24, 8))

        ctk.CTkLabel(
            header,
            text="Wallpaper Fleet Management Hub",
            font=(FONT_FAMILY, 18, "bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Publish a new wallpaper to every machine in the fleet.",
            font=(FONT_FAMILY, 12),
            text_color="#9AA0A6",
        ).pack(anchor="w", pady=(2, 0))

        # --- Card: Target Wallpaper ----------------------------------
        card = ctk.CTkFrame(root, corner_radius=14)
        card.pack(fill="x", padx=24, pady=16)

        ctk.CTkLabel(
            card,
            text="TARGET WALLPAPER",
            font=(FONT_FAMILY, 11, "bold"),
            text_color="#9AA0A6",
        ).pack(anchor="w", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            card,
            text="Wallpaper Image File",
            font=(FONT_FAMILY, 12),
        ).pack(anchor="w", padx=20, pady=(6, 4))

        path_box = ctk.CTkFrame(card, fg_color="transparent")
        path_box.pack(fill="x", padx=20, pady=(0, 4))
        path_box.grid_columnconfigure(0, weight=1)

        self.entry_path = ctk.CTkEntry(
            path_box,
            textvariable=self.image_path,
            placeholder_text="No file selected",
            height=36,
            corner_radius=8,
        )
        self.entry_path.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            path_box,
            text="Browse",
            width=90,
            height=36,
            corner_radius=8,
            command=self.browse_image,
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            card,
            text="Update Note",
            font=(FONT_FAMILY, 12),
        ).pack(anchor="w", padx=20, pady=(14, 4))

        self.entry_msg = ctk.CTkEntry(
            card,
            height=36,
            corner_radius=8,
        )
        self.entry_msg.pack(fill="x", padx=20, pady=(0, 20))
        self.entry_msg.insert(0, "Fleet wallpaper update")

        # --- Push button ------------------------------------------------
        self.btn_push = ctk.CTkButton(
            root,
            text="Push to Fleet",
            font=(FONT_FAMILY, 13, "bold"),
            height=44,
            corner_radius=10,
            fg_color=ACCENT_GREEN,
            hover_color=ACCENT_GREEN_HOVER,
            command=self.push,
        )
        self.btn_push.pack(fill="x", padx=24, pady=(4, 8))

        # --- Status line --------------------------------------------------
        self.status_label = ctk.CTkLabel(
            root,
            text="",
            font=(FONT_FAMILY, 11),
            text_color="#9AA0A6",
        )
        self.status_label.pack(pady=(0, 12))

    def browse_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Wallpaper Image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")],
        )
        if file_path:
            self.image_path.set(file_path)

    def push(self) -> None:
        path = self.image_path.get().strip()
        msg = self.entry_msg.get().strip() or "Wallpaper update"

        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Please select a valid wallpaper image file.")
            return

        try:
            self.btn_push.configure(state="disabled", text="Pushing...")
            self.status_label.configure(text="Publishing update to the fleet...")
            self.root.update()

            controller_main.push_wallpaper(path, msg)

            messagebox.showinfo("Success", "Fleet update published successfully!")
            self.image_path.set("")
            self.status_label.configure(text="Last push succeeded.")
        except Exception as e:
            messagebox.showerror("Deployment Failed", str(e))
            self.status_label.configure(text="Last push failed.")
        finally:
            self.btn_push.configure(state="normal", text="Push to Fleet")


def main() -> int:
    root = ctk.CTk()
    app = ControllerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())