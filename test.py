import tkinter as tk

class CustomListbox:
    def __init__(self, master):
        self.master = master
        self.master.title("Custom Listbox")

        # Création d'un champ de filtre
        self.filter_entry = tk.Entry(self.master)
        self.filter_entry.pack()

        # Création d'une scrollbar
        self.scrollbar = tk.Scrollbar(self.master)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Création d'une liste de frames
        self.listbox = tk.Listbox(self.master, yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Ajout des éléments à la liste de frames
        for i in range(50):
            # Création d'un élément avec une frame personnalisée
            item_frame = CustomListboxItem(self.listbox)
            item_frame.label.config(text=f"Element {i}")
            item_frame.pack(fill=tk.X)

            # Ajout de l'élément à la liste de frames
            self.listbox.insert(tk.END, item_frame)

        # Configuration de la scrollbar
        self.scrollbar.config(command=self.listbox.yview)

        # Configuration du champ de filtre
        self.filter_entry.bind("<KeyRelease>", self.filter_list)

    def filter_list(self, event):
        # Récupération du texte saisi dans le champ de filtre
        filter_text = self.filter_entry.get().lower()

        # Récupération de tous les éléments de la liste de frames
        all_items = [self.listbox.item(index)["values"][0] for index in range(self.listbox.size())]

        # Filtrage des éléments qui correspondent au texte saisi
        filtered_items = [item for item in all_items if filter_text in item.lower()]

        # Mise à jour de la liste de frames avec les éléments filtrés
        self.listbox.delete(0, tk.END)
        for item in filtered_items:
            self.listbox.insert(tk.END, item)

class CustomListboxItem(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Création d'un label
        self.label = tk.Label(self)
        self.label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Création d'un bouton
        self.button = tk.Button(self, text="Click me!")
        self.button.pack(side=tk.RIGHT)

if __name__ == "__main__":
    root = tk.Tk()
    CustomListbox(root)
    root.mainloop()
