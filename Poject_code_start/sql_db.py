import sqlite3


class SQLDB:
    def __init__(self):
        """
        creates the table
        """
        self.DB_name = "GolDrive.sql"
        self.conn = None
        self.curr = None
        self._create_table()

    def _create_table(self):
        """
        create table
        :return:
        """
        self.conn = sqlite3.connect(self.DB_name)
        self.curr = self.conn.cursor()
        sql = "CREATE TABLE IF NOT EXISTS users (username VARCHAR(10) PRIMARY KEY," \
              " password VARCHAR(10), email VARCHAR(50))"
        self.curr.execute(sql)
        self.conn.commit()

    def _username_exist(self, username):
        """
        :param username: username
        :return: True or False if username is in table
        """
        sql = "SELECT username FROM users WHERE username = ?"
        self.curr.execute(sql, (username,))
        return self.curr.fetchone()

    def add_user(self, username, password, email):
        """
        :param username: username
        :param password: password
        :param email: email
        :return: adds user to table
        """
        if not self._username_exist(username):
            sql = "INSERT INTO users VALUES (?,?,?)"
            self.curr.execute(sql, (username, password, email))
            self.conn.commit()

    def delete_user(self, username):
        """
        delete user if exists
        :param username:
        :return:
        """
        if self._username_exist(username):
            sql = "DELETE FROM players WHERE username = ?"
            self.curr.execute(sql, (username,))
            self.conn.commit()

    def correct_password(self, username, password):
        """
        check if user password is correct
        :param username:
        :param password:
        :return: True or False
        """
        if self.username_exist(username):
            sql = "SELECT password FROM users WHERE username = ?"
            self.curr.execute(sql, (username,))
            actual_password, = self.curr.fetchone()
            return actual_password == password

    def get_wins(self, username):
        """
        return the user's wins if exists
        :param username:
        :return: wins
        """
        if self.username_exist(username):
            sql = "SELECT wins FROM users WHERE username = ?"
            self.curr.execute(sql, (username,))
            wins, = self.curr.fetchone()
            return wins

    def get_all_wins(self):
        """
        return a dictionary of all users' usernames and their wins
        :return: dictionary of all users' usernames and their wins in a tuple
        """
        sql = "SELECT username, wins FROM users"
        self.curr.execute(sql)
        lst = self.curr.fetchall()
        return lst

    def update_win(self, username, time):
        """
        update the user's wins if it's better than the current one
        :param username:
        :param time:
        :return:
        """""
        if self.username_exist(username):
            wins = int(self.get_wins(username))
            if wins == 0 or wins > time:
                sql = f"UPDATE users SET wins = {time} WHERE username = ?"
                self.curr.execute(sql, (username,))
                self.conn.commit()

