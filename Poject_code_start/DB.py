import sqlite3


class DB:
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
        flag = 1
        if not self._username_exist(username):
            sql = "INSERT INTO users VALUES (?,?,?)"
            self.curr.execute(sql, (username, password, email))
            self.conn.commit()

            flag = 0
        return flag

    def delete_user(self, username):
        """
        :param username: username
        :return: delets user
        """
        flag = 1
        if self._username_exist(username):
            sql = "DELETE FROM users WHERE username = ?"
            self.curr.execute(sql, (username,))
            self.conn.commit()

            flag = 0
        return flag

    def get_password(self, username):
        """
        :param username: username
        :return: users password
        """
        if self._username_exist(username):
            sql = "SELECT password FROM users WHERE username = ?"
            self.curr.execute(sql, (username,))
            password, = self.curr.fetchone()
            return password

    def get_email(self, username):
        """
        :param username: username
        :return: users email
        """
        if self._username_exist(username):
            sql = "SELECT email FROM users WHERE username = ?"
            self.curr.execute(sql, (username,))
            email, = self.curr.fetchone()
            return email

    def change_username(self, username, newname):
        """
        :param username: username
        :param newname: name to change to
        :return: changes username
        """
        flag = 1
        if self._username_exist(username):
            sql = f"UPDATE users SET username = ? WHERE username = ?"
            self.curr.execute(sql, (newname, username,))
            self.conn.commit()

            flag = 0
        return flag

    def change_password(self, username, password):
        """
        :param username: username
        :param password: password to change to
        :return: changes password
        """
        flag = 1
        if self._username_exist(username):
            sql = f"UPDATE users SET password = ? WHERE username = ?"
            self.curr.execute(sql, (password, username,))
            self.conn.commit()

            flag = 0
        return flag

    def change_email(self, username, email):
        """
        :param username: username
        :param email: email to change to
        :return: changes email
        """
        flag = 1
        if self._username_exist(username):
            sql = f"UPDATE users SET email = ? WHERE username = ?"
            self.curr.execute(sql, (email, username,))
            self.conn.commit()

            flag = 0
        return flag


if __name__ == '__main__':
    s = DB()
    s.delete_user("reef")
