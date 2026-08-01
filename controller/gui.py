"""
controller/gui.py

Single-Operator Wallpaper Fleet Controller.
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from . import config
from . import main as controller_main


class ControllerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Wallpaper Fleet Controller")
        self.root.geometry("450x260")
        self.root.resizable(False, False)

        self.image_path = tk.StringVar()

        # UI Layout
        tk.Label(root, text="Wallpaper Fleet Management Hub", font=("Arial", 12, "bold")).pack(pady=10)

        # Image Selection Frame
        frame_img = tk.LabelFrame(root, text=" Target Wallpaper ", font=("Arial", 9, "bold"))
        frame_img.pack(fill="x", padx=20, pady=10, ipadx=10, ipady=10)

        tk.Label(frame_img, text="Wallpaper Image File:").pack(anchor="w")
        
        path_box = tk.Frame(frame_img)
        path_box.pack(fill="x", pady=5)
        tk.Entry(path_box, textvariable=self.image_path, width=35).pack(side="left", padx=(0, 5))
        tk.Button(path_box, text="Browse", command=self.browse_image).pack(side="left")

        tk.Label(frame_img, text="Update Note:").pack(anchor="w", pady=(5, 0))
        self.entry_msg = tk.Entry(frame_img, width=47)
        self.entry_msg.pack(pady=5)
        self.entry_msg.insert(0, "Fleet wallpaper update")

        # Push Button
        self.btn_push = tk.Button(root, text="Push to Fleet", bg="#28a745", fg="white", font=("Arial", 10, "bold"), command=self.push)
        self.btn_push.pack(pady=10, ipadx=15, ipady=3)

    def browse_image(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Wallpaper Image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
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
            self.btn_push.config(state="disabled", text="Pushing...")
            self.root.update()

            controller_main.push_wallpaper(path, msg)

            messagebox.showinfo("Success", "Fleet update published successfully!")
            self.image_path.set("")
        except Exception as e:
            messagebox.showerror("Deployment Failed", str(e))
        finally:
            self.btn_push.config(state="normal", text="Push to Fleet")


def main() -> int:
    root = tk.Tk()
    app = ControllerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())