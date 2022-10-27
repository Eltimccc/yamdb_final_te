import csv
import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

TABLE_PREFIX = "reviews"
FILES_TBLS_LIST = {
    "genre.csv": [f"{TABLE_PREFIX}_genre", 0],
    "category.csv": [f"{TABLE_PREFIX}_category", 0],
    "comments.csv": [f"{TABLE_PREFIX}_comment", 1],
    "review.csv": [f"{TABLE_PREFIX}_review", 1],
    "titles.csv": [f"{TABLE_PREFIX}_title", 1],
    "genre_title.csv": [f"{TABLE_PREFIX}_title_genre", 1],
    "users.csv": [f"{TABLE_PREFIX}_user", 1],
}
PATH_TO_CSV = os.path.join(settings.BASE_DIR, "static", "data")
FLD_TITLES_TO_CHANGE = {"category": "category_id", "author": "author_id"}


class Command(BaseCommand):
    help = "Import data from csv files to DB"

    def handle(self, *args, **options):
        cursor = connection.cursor()
        # Временно отключаем внешние ключи.
        cursor.execute("PRAGMA foreign_keys = OFF;")
        files_csv_list = os.listdir(PATH_TO_CSV)

        for file_name in files_csv_list:
            if file_name in FILES_TBLS_LIST.keys():
                tbl_t = FILES_TBLS_LIST[file_name][0]
                header_in_query = FILES_TBLS_LIST[file_name][1]
                file = os.path.join(PATH_TO_CSV, file_name)
                with open(file, newline="", encoding="utf-8") as csvfile:
                    csv_reader = csv.reader(csvfile, delimiter=",")
                    row_num = 0
                    for row in csv_reader:
                        if row_num == 0:
                            sql_hdr = self.header_handler(
                                row, header_in_query, tbl_t, file_name
                            )
                        else:
                            sql_fld_values = self.data_handler(row, file_name)
                            sql_body_final = (
                                f"{sql_hdr} VALUES ({sql_fld_values})"
                            )
                            cursor.execute(sql_body_final)
                        row_num += 1
        # Включаем внешние ключи.
        cursor.execute("PRAGMA foreign_keys = ON;")
        self.stdout.write(self.style.SUCCESS("Импорт данных завершен!"))

    def header_handler(self, row, header_in_query, tbl_t, file_name):
        """
        Создание заголовочной части тела запроса.
        """

        if header_in_query == 1:
            for k in FLD_TITLES_TO_CHANGE.keys():
                if k in row:
                    cur_i = row.index(k)
                    row[cur_i] = FLD_TITLES_TO_CHANGE[k]
            if "user" in file_name:
                row.append("password")
                row.append("is_superuser")
                row.append("is_staff")
                row.append("is_active")
                row.append("date_joined")
            sql_hdr = f"INSERT INTO `{tbl_t}` ({', '.join(row)})"
        else:
            sql_hdr = f"INSERT INTO `{tbl_t}`"
        return sql_hdr

    def data_handler(self, row, file_name):
        """
        Создание основной части тела запроса.
        """

        vals = ""
        if len(row) == 1:
            # Разделитель в данных
            if row[0][0] == '"' and row[0][-1] == '"':
                row[0] = row[0][1:-1]
            row = re.split(
                """,
                (?=(?:[^'"]|'[^']*'|"[^"]*")*$)""",
                row[0],
            )
        for w in row:
            if w.isnumeric():
                vals += f"{w}, "
            else:
                w = w.replace("'", "%27")
                vals += f"'{w}', "
        if "user" in file_name:
            vals += "'0', "
            vals += "'no', "
            vals += "'no', "
            vals += "'yes', "
            vals += "'2022-09-16T21:08:21.567Z', "
        sql_fld_values = vals[0:-2]
        return sql_fld_values
