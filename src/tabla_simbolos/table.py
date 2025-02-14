class Table:
    """Represents a symbol table.

    Args:
        id_ (int): Set the identifier of this table.

    Attributes:
        lexems (list of dict): A list which represents the lexems in the table.
        exists (bool): Represents if the table exists or not.
        id_ (int): The identifier of the table.

    """

    def __init__(self, id_):
        self.lexems = []
        self.exists = True
        self.id_ = id_

    def exist(self):
        """Checks if the symbol table exists.

        Returns:
            bool: True if it exists, False otherwise.
        """
        return self.exists

    def delete(self):
        """Marks the table as deleted"""
        self.exists = False

    def contains_lex(self, lex):
        """Checks if lex is in the table.

        Args:
            lex (str): The lexeme to find in the symbol table.

        Returns:
            bool: True if lex exists, False otherwise.
        """

        return True if self.get_pos(lex) else False

    def get_pos(self, lex):
        """Gets the lexeme position in symbol table.

        Args:
            lex (str): The lexeme to find in the symbol table.

        Returns:
             int or None: the position where lex is located, None otherwise.
        """

        for index, dict_ in enumerate(self.lexems):
            if dict_["LEXEMA"] == lex:
                return index

        return None

    def add_lex(self, lex):
        """Add a lexeme into the symbol table.

        Args:
            lex (str): The lexeme to be added.

        Returns:
            int: index in table where lex has been added
        """

        self.lexems.append({"LEXEMA": lex})
        return len(self.lexems) - 1

    def remove_lex_at(self, pos_lex):
        """Removes a lexeme in a given position from the table.

        Args:
            pos_lex (int): The position that is going to be removed.

        Returns:
            dict or None: dict the lexeme deleted, None if index is out of bounds.
        """
        if pos_lex >= len(self.lexems):
            return None

        return self.lexems.pop(pos_lex)

    def add_attribute(self, table_pos, type_, content):
        """Adds an attribute to a lexeme where is located in a position of a table.

        Args:
            table_pos (int): Position of the lexeme in the table.
            type_ (str): The type of attribute to set.
            content (any): The value of the attribute.

        Returns:
            bool: True if the attribute has been added, false otherwise.
        """
        if self.lexems[table_pos].get(type_):
            return False

        self.lexems[table_pos][type_] = content
        return True

    def get_attribute(self, table_pos, type_):
        """Gets value of an attribute of a lexeme.

        Args:
            table_pos (int): Position of the lexeme in the table.
            type_ (str): The type of the attribute.

        Returns:
            any or None: any the value of the attribute if exists, False otherwise.
        """

        return self.lexems[table_pos].get(type_)

    def get_lex_dict(self, lex):
        """Gets the dict of a specified lexeme.

         Returns:
            dict or None: dictionary of lexeme "lex" if exists, None otherwise.
        """
        for entry in self.lexems:
            if entry["LEXEMA"] == lex:
                return entry
        return None

    def get_lex_entry(self, pos_lex):
        """Gets the lexeme which is located in a given position.

        Args:
            pos_lex (int): The index in the table

        Returns:
            dict or None: The lexeme dictionary located into pos_lex, None otherwise.
        """

        if pos_lex >= len(self.lexems):
            return None

        return self.lexems[pos_lex]

    def write(self, file):
        """Prints the content of the table into the file provided.
            Prints the using the format provided in
            FormatoImpresiónTablaDeSímbolos.txt
        Args:
            file (file): File where the TS is going to be written
        """

        to_write = f'CONTENIDO DE LA TABLA # {str(self.id_)} :\n'
        to_write += '\n'
        for dict_ in self.lexems:
            for i, keys in enumerate(dict_.keys()):
                if i == 0:
                    to_write += f'*\t{keys} : \'{dict_[keys]}\''
                elif i == 1:
                    to_write += f'\tATRIBUTOS :\n'
                    to_write += f'\t+ {keys} : \'{dict_[keys]}\''
                else:
                    if keys == 'TipoParam' and dict_['TipoParam'] != 'void':
                        for j, element in enumerate(dict_['TipoParam']):
                            to_write += f'\t+ TipoParam{j + 1} : \'{element}\''
                            to_write += '\n'
                    else:
                        to_write += f'\t+ {keys} : \'{dict_[keys]}\''
                to_write += '\n'
            to_write += f'---------------- ----------------\n'
        to_write += '\n\n\n'

        file.write(to_write)