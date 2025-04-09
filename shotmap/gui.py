"""Graphical user interface for visualizing shotmap data"""

import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import os
import shotmap

def main():
    def window_season_shotmap():
        """Opens new window displaying season shotmap"""
        # Opens new window, when close root, will close this window too
        visualization = tk.Toplevel() 

        # Collect arguments from user entry
        player_name = player_entry.get()
        competition_name = competition_entry.get()

        # Save shotmap visualization as an image
        fig = shotmap.season_shotmap(player_name, competition_name)
        fig.savefig("season_shotmap_preview.png", bbox_inches="tight", dpi=75)
        fig.savefig("season_shotmap_original.png", bbox_inches="tight")
        shotmap_plot = tk.PhotoImage(file="season_shotmap_preview.png")

        # Display the shotmap in the new window
        shotmap_label = tk.Label(visualization, image=shotmap_plot)
        shotmap_label.image = shotmap_plot  # Prevents garbage collection
        shotmap_label.pack()
        plt.close(fig)  # Free up memory
        visualization.resizable(False, False)  # Prevents resizing

        # Add menubar where you can save the visualization as a file to your computer
        menubar = tk.Menu(visualization)
        visualization.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save As", command=lambda: save_file())

    def save_file():
        import shutil
        files = [("PNG files", "*.png")]
        file = filedialog.asksaveasfilename(filetypes=files, defaultextension=files[0][1])
        shutil.copy("season_shotmap_original.png", file)


    root = tk.Tk()  # Instantiates window
    root.resizable(False, False)
    root.geometry("300x150")
    root.title("Football Hub")
    root.config(background="#0C0D0E")

    # Establish 3x2 grid
    tk.Grid.rowconfigure(root, 0, weight=1)
    tk.Grid.rowconfigure(root, 1, weight=1)
    tk.Grid.rowconfigure(root, 2, weight=1)
    tk.Grid.columnconfigure(root, 0, weight=1)
    tk.Grid.columnconfigure(root, 1, weight=1)

    # Title
    title_label = tk.Label(root,
                    text="Football Hub",
                    font=("Arial", 15, "bold"),
                    fg="white",
                    bg="#0C0D0E"
                    ).grid(row=0, column=0, columnspan=2)


    # Player name
    player_label = tk.Label(root,
                    text="Player name:",
                    font=("Arial", 15),
                    fg="black",
                    bg="white",
                    anchor="w",
                    highlightthickness=2,
                    highlightcolor="black"
                    ).grid(row=1, column=0, sticky="nsew")

    player_entry = tk.Entry(width=15,
                    fg="gray",
                    bg="white"
                    )
    player_entry.grid(row=1, column=1, sticky="nsew")
    player_entry.insert(0, "Firstname Lastname")

    def player_on_click(event):
        if player_entry.get() == "Firstname Lastname":
            player_entry.delete(0, tk.END)
            player_entry.config(fg="black")

    def player_on_focus_out(event):
        if player_entry.get() == "":
            player_entry.insert(0, "Firstname Lastname")
            player_entry.config(fg="gray")

    def on_completed_form_1(event):
        if competition_entry.get() != "Competition YY/YY" and competition_entry.get() != "":
            window_season_shotmap()

    player_entry.bind('<FocusIn>', player_on_click)
    player_entry.bind('<FocusOut>', player_on_focus_out)
    player_entry.bind('<Return>', on_completed_form_1)


    # Competition name
    competition_label = tk.Label(root,
                    text="Competition name:",
                    font=("Arial", 15),
                    fg="black",
                    bg="white",
                    anchor="w",
                    highlightthickness=2,
                    highlightcolor="black"
                    ).grid(row=2, column=0, sticky="nsew")

    competition_entry = tk.Entry(width=15,
                    fg="gray",
                    bg="white",
                    )
    competition_entry.grid(row=2, column=1, sticky="nsew")
    competition_entry.insert(0, "Competition YY/YY")

    def player_on_click(event):
        if competition_entry.get() == "Competition YY/YY":
            competition_entry.delete(0, tk.END)
            competition_entry.config(fg="black")

    def player_on_focus_out(event):
        if competition_entry.get() == "":
            competition_entry.insert(0, "Competition YY/YY")
            competition_entry.config(fg="gray")

    def on_completed_form_2(event):
        if player_entry.get() != "Firstname Lastname" and player_entry.get() != "":
            window_season_shotmap()

    competition_entry.bind('<FocusIn>', player_on_click)
    competition_entry.bind('<FocusOut>', player_on_focus_out)
    competition_entry.bind('<Return>', on_completed_form_2)


    # Enter button
    enter_button = tk.Button(root,
                    text="Enter",
                    fg="black",
                    bg="white",
                    activeforeground="black",
                    activebackground="white",
                    command=window_season_shotmap
                    ).grid(row=3,column=0, columnspan=2, sticky="s")


    # Delete image from directory when close root window
    def close_window():
        os.remove("season_shotmap_preview.png")
        os.remove("season_shotmap_original.png")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_window)


    root.mainloop()


if __name__ == "__main__":
    main()