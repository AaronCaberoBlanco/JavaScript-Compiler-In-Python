from src.tabla_simbolos.table import Table


class SymTable:
    """Represents a handler of symbol tables.

    Attributes:
        tables (list of Table): Contains the different tables.
        nextId (int): The next number which a new table will take to identify itself.

    """

    def __init__(self):
        self.tables = []
        self.nextId = 0

    def exist_table(self, table_index):
        """Checks if the table symbol identified by table_index exists.

        Args:
            table_index (int): The identifier of the symbol table.

        Returns:
            bool: True if it exists, False otherwise.
        """
        a = self.tables[table_index]
        return a and a.exist()

    def destroy_table(self, table_index):
        """Destroys a symbol table identified by table_index.

        Args:
            table_index (int): The identifier of the symbol table.
        """
        self.tables[table_index].delete()

    def exists_entry(self, table_index, lex):
        """Checks if lex is in the table identified by table_index.

        Args:
            table_index (int): Identifier of the symbol table.
            lex (str): The lexem to be found in the symbol table.

        Returns:
            bool: True if lex exists, False otherwise.
        """
        return self.tables[table_index].contains_lex(lex)

    def new_table(self):
        """Creates a new symbol table.

        Returns:
            nextId: The identifier of the new symbol table.
        """

        self.tables.append(Table(self.nextId))
        self.nextId += 1
        return self.nextId - 1

    def get_pos(self, lex):
        """Gets the position of the table where lex is located.

        Args:
            lex (str): The lexeme to be found in the symbol table

        Returns:
           int, int or None, None: the table index and the position in that table where lex is located or None otherwise
        """
        id_table = None
        id_pos = None
        for index, elem in reversed(list(enumerate(self.tables))):
            if elem.exists:
                id_pos = self.tables[index].get_pos(lex)
                if id_pos is not None:
                    id_table = index
                    break

        return id_table, id_pos

    def get_local_pos(self, lex):
        """Gets the position of the local table where lex is located.

        Args:
            lex (str): The lexeme to be found in the symbol table

        Returns:
           int, int or None, None: the table index and the position in that table where lex is located or None otherwise
        """
        id_table = None
        id_pos = None
        for index, elem in reversed(list(enumerate(self.tables))):
            if elem.exists:
                id_pos = self.tables[index].get_pos(lex)
                if id_pos is not None:
                    id_table = index
                break

        return id_table, id_pos

    def add_entry(self, lex):
        """Adds lex to the last symbol table created.

        Args:
            lex (str): The lexeme to add_entry in the symbol table.

        Returns:
            int, int or None, None: the table index and the position in that table where lex has been added or None otherwise
        """
        id_table = None
        id_pos = None

        for index, elem in reversed(list(enumerate(self.tables))):
            if elem.exists:
                id_table = index
                id_pos = self.tables[index].add_lex(lex)
                break

        return id_table, id_pos

    def add_global_entry(self, lex):
        """Adds a lexeme into the global symbol table.

        Args:
            lex (str): The lexeme to be added in the symbol table.

        Returns:
            int, int or None, None: the table index and the position in that table where lex has been added or None otherwise
        """
        id_table = None
        id_pos = None

        for index, elem in list(enumerate(self.tables)):
            if elem.exists:
                id_table = index
                id_pos = self.tables[index].add_lex(lex)
                break

        return id_table, id_pos

    def remove_lex_at(self, id_table, pos_lex):
        """Removes a lexeme located in pos_lex from the table identified by id_table.

        Args:
            id_table (int): Represents the identifying of the symbol table.
            pos_lex (int): The position that is going to be removed.

        Returns:
            dict or None: The lexeme deleted, None if index is out of bounds.
        """
        return self.tables[id_table].remove_lex_at(pos_lex)

    def add_attribute(self, table_index, table_pos, type_, content):
        """Adds an attribute to a lexeme in the table identified by table_index and indexed by table_pos.

        Args:
            table_index (int): Table index in the symbol table.
            table_pos (int): Position of the lexeme in the table.
            type_ (str): The type of attribute to set.
            content (any): The value of the attribute.

        Returns:
            bool: True if the attribute has been added, false otherwise.
        """
        return self.tables[table_index].add_attribute(table_pos, type_, content)

    def get_attribute(self, table_index, table_pos, type_):
        """Gets value of an attribute of a lexeme in the table identified by table_index and indexed by table_pos.

        Args:
            table_index (int): Table index in the symbol table.
            table_pos (int): Position of the lexeme in the table.
            type_ (str): The type of attribute to get.

        Returns:
             any or None: the value of the type_, False if the type does not exist.
        """
        return self.tables[table_index].get_attribute(table_pos, type_)

    def get_lex_dict(self, table_index, lex):
        """Gets the dict of a specified lexeme stored in the table identified by table_index.
         Args:
            table_index (int): Represents the identifying of the symbol table.
            lex (str): The lexem located in the table
         Returns:
            dict or None: dictionary of lex, None if lex isn't located in table.
        """
        return self.tables[table_index].get_lex_dict(lex)

    def get_lex_entry(self, table_index, pos_lex):
        """Gets the lexem entry located in the table identified by table_index

        Args:
            table_index (int): Represents the identifying of the symbol table.
            pos_lex (int): The position into the table

        Returns:
            dict or None: dict lexeme located at pos_lex, None if otherwise
        """

        return self.tables[table_index].get_lex_entry(pos_lex)

    #TODO: Comment method
    def is_global(self, var):
        return True if var[0] == 0 else False

    def write_table(self, file):
        """Prints the content of all the tables to the specified file.
            Prints the tables using the format in FormatoImpresiónTablaDeSímbolos.txt
        Args:
            file (File): the file where the content is going to be written

        Returns:
            bool: True if the table exists. False otherwise.
        """
        for tab in self.tables:
            tab.write(file)
        return True
