# Copyright (C) 2023 Julien LE THENO
#
# This file is part of the VLCSequencer package
# See github.com/lethenju/VLCSequencer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import sqlite3
from threading import Thread
from logger import PrintTraceInUi
import time
import copy

_data_manager = None


def GetDataManager():
    """! Returns the DataManager instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager("internal.dat")
    return _data_manager


class DataManager:
    """! Data Manager modules
        Connects with a sqlite db for internal
        persisted data between launches in a generic way

        Creates a db if it doesnt exist
        loads a db
        get some data
        insert some data
        check if a table exists
        creates a table
    """
    path = ""
    _db_connection = None
    _db_cursor = None
    _is_running = True
    _fifo_messages = []
    _data_thread = None
    _results_from_thread = []

    def _thread_runtime(self):
        self._db_connection = sqlite3.connect(self.path)
        self._db_cursor = self._db_connection.cursor()

        while self._is_running:
            if self._fifo_messages:
                fifo_messages = copy.copy(self._fifo_messages)
                self._fifo_messages = []
                for message in fifo_messages:
                    if message[0] == "CREATE":
                        # Create
                        self._db_cursor.execute(message[1])
                    if message[0] == "INSERT":
                        self._db_cursor.executemany(message[1], message[2])
                        self._db_connection.commit()
                    if message[0] == "IS_EXIST":
                        result = False
                        list_of_tables = self._db_cursor. \
                            execute(message[1]).fetchall()
                        if list_of_tables:
                            result = True
                        self._results_from_thread.append(result)
                    if message[0] == "SELECT":
                        res = self._db_cursor.execute(message[1])
                        self._results_from_thread. \
                            append(copy.copy(res.fetchall()))
            # Argh.. not very efficient
            time.sleep(0.2)

    def __init__(self, path):
        self.path = path
        self._is_running = True
        self._data_thread = Thread(target=self._thread_runtime)
        self._data_thread.start()

    def kill(self):
        PrintTraceInUi("Killing the data manager")
        self._is_running = False
        self._data_thread.join()

    def create_table(self, table_name, table_columns_list):
        """! Creates a sqlite table
            @param table_name    name of the table to be created
            @param table_columns list of the table columns
        """
        query_str = "CREATE TABLE " + table_name + "("
        columns_str = ""
        for k, column in enumerate(table_columns_list):
            if k < len(table_columns_list) - 1:
                # This is not the last item
                columns_str = columns_str + column + ", "
            else:
                # This is the last item
                columns_str = columns_str + column + ")"
        query_str = query_str + columns_str
        PrintTraceInUi(f"Query str = {query_str}")
        # self._db_cursor.execute(query_str)
        self._fifo_messages.append((["CREATE", query_str]))

    def is_table_exists(self, table_name):
        """! Returns true if a table exist
            @param table_name the name of the table to check
            @return true if the table exist, false otherwise
        """
        query_str = f"SELECT name FROM sqlite_master \
            WHERE type='table' AND name='{table_name}';"
        self._fifo_messages.append((["IS_EXIST", query_str]))
        # Wait for _results_from_thread
        while not self._results_from_thread and self._is_running:
            time.sleep(0.1)
        if self._results_from_thread:
            # TODO Check if the result is made for us
            result = self._results_from_thread.pop()
            self._results_from_thread = []
            return result

    def insert_entries(self, table_name, entries_list):
        """! Insert lines in a sqlite table
            @param table_name the name of the table to add entry to
            @param entries_list the list of
                   arguments to fill the columns of the entry
                    ex : [
                          ('John Doe', 4),
                          ('Toto', 6),
                         ]
        """

        if not self.is_table_exists(table_name):
            PrintTraceInUi(f"The table {table_name} does NOT exist !")
            return

        query_str = "INSERT INTO " + table_name + " VALUES ("
        columns_str = ""
        # Placing placeholders
        for k in range(len(entries_list[0])):
            if k < len(entries_list[0]) - 1:
                # This is not the last item
                columns_str = columns_str + "?, "
            else:
                # This is the last item
                columns_str = columns_str + "?)"
        query_str = query_str + columns_str
        PrintTraceInUi(f"Query str = {query_str}")
        self._fifo_messages.append((["INSERT", query_str, entries_list]))

    def select_entries(self, table_name, columns,  **kwargs):
        """! Select lines in a sqlite table
            @param table_name the name of the table to add entry to
            @param columns : columns to retrieve. Can be '*' to get everything
            @param OPTIONAL : order_by : orders the list with the given column

            @return a list of the entries
        """
        query_str = "SELECT " + columns + " FROM " + table_name
        if "order_by" in kwargs:
            query_str = query_str + " ORDER BY " + kwargs["order_by"]

        PrintTraceInUi(f"Query str = {query_str}")
        self._fifo_messages.append(["SELECT", query_str])
        # Wait for _results_from_thread
        while not self._results_from_thread and self._is_running:
            time.sleep(0.1)
        if self._results_from_thread:
            # TODO Check if the result is made for us
            result = self._results_from_thread.pop()
            self._results_from_thread = []
            return result
