import os
import random
import time
import types
import uuid

import pytest
import select
import subprocess

from typing import Callable, Optional, List, Union, Dict
from dataclasses import dataclass
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import errors


random.seed(42)

# TODO:
#  Replace all time.sleep
#  Replace book_tags with tags after fixing in current solution



# TODO:
#   DeleteAuthor
#       For authors withoud books           - Ok
#       For authors with books              - requires fixes in current solution
#       Canceling                           - requires fixes
#       Failed deletion non-existent author - Ok
#   EditAuthor
#       By Name      - Ok
#       By Index     - Ok
#       Canceling    - Failed to edit
#       Non-existing - Ok
#   ShowBooks
#       Ok
#   ShowBook
#       By name      - Ok
#       By index     - Ok
#       Gl index     - Ok
#       Canceling    - Ok
#       Non-existing - Shows empty line instead of 'Book not found'
#   DeleteBooks
#       By name      - Ok
#       By index     - Ok
#       Gl index     - Ok
#       Canceling    - Ok
#       Non-existing - Shows empty line instead of 'Book not found'
#   EditBook
#       By name      - Ok
#       By index     - Ok
#       Gl index     - Ok
#       Partial      - Not ok...
#       Canceling    - Book not found
#       Non-existing - Ok
#   Concurrency


def create_random_name():
    names = [
        'Bob', 'Kevin', 'Roberto', 'Quill', 'Patrick', 'Luciano', 'Zelda', 'Patricia', 'Sara'
    ]
    surnames = [
        'Fox', 'Gallagher', 'The Bull', 'The third', 'Spalletti', 'Brown', 'The greatest', ''
    ]
    additions = [
        '',  'Great', 'Superpowered', 'Fictional', 'Egocentric'
    ]
    author: str = random.choice(additions) + ' ' + random.choice(names) + ' ' + random.choice(surnames)
    author = author.strip()
    return author


def create_new_name(db_name):
    attempt = create_random_name()
    try:
        authors = [pair[1] for pair in get_authors(db_name)]
    except psycopg2.errors.UndefinedTable:
        authors = []

    while attempt in authors:
        attempt = create_random_name()

    return attempt


def create_messy_tags(count: Optional[int] = 20):
    tags = ['tag 1', 'romantic', 'pedantic', 'horror', 'for adults', 'for children']
    bad_tags = ['', '      ', '    spaaaaces   ', ', , , , ', ' #']
    bad_count = random.randint(0, count - 1)
    chosen = [random.choice(tags) for _ in range(count - bad_count)]
    chosen.extend([random.choice(bad_tags) for _ in range(bad_count)])
    chosen.append(random.choice(chosen))  # To ensure there is at least one duplicate
    result = ''
    for tag in chosen:
        result += tag + ', '
    return result


def get_connection(db_name):
    return psycopg2.connect(user=os.environ['POSTGRES_USER'],
                            password=os.environ['POSTGRES_PASSWORD'],
                            host=os.environ['POSTGRES_HOST'],
                            port=os.environ['POSTGRES_PORT'],
                            dbname=db_name,
                            cursor_factory=DictCursor,
                            )


def authors_to_str(authors):
    return [f'{i+1} {author["name"]}'.strip() for i, author in enumerate(authors)]


def books_to_str(books):
    return [f'{i+1} {book["title"]} by {book["name"]}, {book["publication_year"]}'.strip() for i, book in enumerate(books)]


def book_to_str(book: List[str]) -> List[str]:
    result = list()
    result.append('Title: ' + book[1])
    result.append('Author: ' + book[2])
    result.append('Publication year: ' + str(book[3]))
    if len(book) == 5:
        tags = book[4].split(',')
        tags = [tag.strip() for tag in tags]
        tags.sort()
        sorted_tags = ''
        for tag in tags:
            sorted_tags += tag + ', '
        sorted_tags = sorted_tags[:-2]  # Dumb way to get rid of ", " on the end
        result.append('Tags: ' + sorted_tags)

    return result


def get_authors(db_name):
    query = "SELECT id, name FROM authors ORDER BY name;"
    with get_connection(db_name) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def get_books(db_name):
    query = """SELECT
    books.id AS book_id,
    title,
    author_id,
    authors.name AS name,
    publication_year
FROM books
INNER JOIN authors ON authors.id = author_id
ORDER BY title, name, publication_year
;"""
    with get_connection(db_name) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def get_author_books(db_name, author_id):
    query = """SELECT
    id,
    title,
    author_id,
    publication_year 
FROM books
WHERE author_id=%s
ORDER BY publication_year, title
;"""
    with get_connection(db_name) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (author_id,))
            return [f'{i+1} {book["title"]}, {book["publication_year"]}'.strip() for i, book in enumerate(cur.fetchall())]


def get_book(db_name, title):

    # FIXME:
    #  В текущем решении указана таблица book_tags вместо tags,
    #  что не соответствует заданию!!!

    query = """SELECT
    books.id AS book_id,
    title,
    name,
    publication_year,
    grouped_tags.tags
FROM books
INNER JOIN authors ON authors.id = author_id
INNER JOIN (
    SELECT
        book_id,
        STRING_AGG(tag, ', ') AS tags
    FROM book_tags
    GROUP BY book_tags.book_id
) AS grouped_tags
ON grouped_tags.book_id = books.id
WHERE title=%s
;"""
#     query = """SELECT
#     books.id AS book_id,
#     title,
#     name,
#     publication_year,
#     grouped_tags.tags
# FROM books
# INNER JOIN authors ON authors.id = author_id
# INNER JOIN (
#     SELECT
#         book_id,
#         STRING_AGG(tag, ', ') AS tags
#     FROM book_tags
#     GROUP BY book_tags.book_id
# ) AS grouped_tags
# ON grouped_tags.book_id = books.id
# WHERE title=%s
# ;"""


    with get_connection(db_name) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (title,))
            res = cur.fetchall()
            count = 15
            while res == [] and count:
                cur.execute(query, (title,))
                res = cur.fetchall()
                print(res, query, title)
                count -= 1
            return res


@dataclass
class Bookypedia:
    process: subprocess.Popen
    db_name: str
    chose: Optional[str] = None

    @staticmethod
    def random_chooser(authors):
        index = random.randint(0, len(authors)-1)
        return index+1, authors[index]

    @staticmethod
    def index_chooser(index: int):
        def chooser(authors):
            return index+1, authors[index]
        return chooser

    @staticmethod
    def empty_chooser(authors):  # To test canceling
        return '', ''

    @staticmethod
    def get_index_by_author(db_name, author):
        authors = authors_to_str(get_authors(db_name))
        for i, string in enumerate(authors):
            if string.find(author) != -1:
                return i + 1

    @staticmethod
    def book_chooser(author):
        def chooser(books: List[str]):
            for i, book in enumerate(books):
                if book.find(author) != -1:
                    return i + 1, book

        return chooser

    def _wait_select(self, timeout=0.2):
        delta = timeout/100
        for _ in range(100):
            if select.select([self.process.stdout], [], [], 0.0)[0]:
                return True
            time.sleep(delta)
        return False

    def _wait_strings(self, timeout=0.2):
        res = list()
        if self._wait_select(timeout):
            delta = timeout/100
            for _ in range(100):
                line = self.process.read()
                if line:
                    res.append(line)
                time.sleep(delta)
        return res

    def add_author(self, author: Optional[str]) -> Optional[str]:
        if author:
            self.process.write(f'AddAuthor {author}')
        else:
            self.process.write(f'AddAuthor')
        if self._wait_select():
            return self.process.read()

    def show_authors(self) -> List[str]:
        self.process.write('ShowAuthors')
        return self._wait_strings()

    def _author(self, command, author_or_callback: Union[str, Callable]) -> Optional[str]:
        if isinstance(author_or_callback, str):
            self.process.write(f'{command} {author_or_callback}')
        else:
            self.process.write(command)
            authors = self._wait_strings()[1:-1]
            if authors:
                number, self.chose = author_or_callback(authors)
                self.process.write(f'{number}')
            else:
                self.process.write('')
                return None
        if self._wait_select():
            return self.process.read()

    def delete_author(self, author_or_callback: Union[str, Callable]) -> Optional[str]:
        return self._author('DeleteAuthor', author_or_callback)

    def edit_author(self, author_or_callback: Union[str, Callable], new_author: str) -> Optional[str]:
        request = self._author('EditAuthor', author_or_callback)  # Enter new name:
        if author_or_callback == self.empty_chooser:
            return request
        if request.startswith('Failed'):
            return request
        self.process.write(new_author)
        if self._wait_select():
            return self.process.read()

    def _book(self, command: str, book: Optional[str], callback: Optional[Callable]) -> List[str]:

        # Using title
        if isinstance(book, str):
            self.process.write(f'{command} {book}')
            books = self._wait_strings()
            if books:
                # More than one book with this title
                if books[0].startswith('1'):
                    if callback:
                        number, self.chose = callback(books)
                    else:
                        self.chose = books[0]
                        number = 1
                    self.process.write(f'{number}')
                else:
                    return books
        # Using callback only
        else:
            self.process.write(command)
            books = self._wait_strings()[:-1]
            if books:
                number, self.chose = callback(books)
                self.process.write(f'{number}')

        return self._wait_strings()

    def __book(self, command: str, book_or_callback: Union[str, Callable]) -> List[str]:
        if isinstance(book_or_callback, str):
            self.process.write(f'{command} {book_or_callback}')
            books = self._wait_strings()
            if books:
                if books[0].startswith('1'):
                    self.chose = books[0]
                    self.process.write('1')
                else:
                    return books
        else:
            self.process.write(command)
            books = self._wait_strings()[:-1]
            if books:
                number, self.chose = book_or_callback(books)
                self.process.write(f'{number}')
        return self._wait_strings()

    def show_book(self, book: Optional[str] = None, callback: Optional[Callable] = None) -> List[str]:
        return self._book('ShowBook', book, callback)

    def delete_book(self, book: Optional[str] = None, callback: Optional[Callable] = None) -> List[str]:
        return self._book('DeleteBook', book, callback)

    def edit_book(self, book: Optional[str] = None, callback: Optional[Callable] = None, new_info: Dict[str, str] = None) -> List[str]:
        mb_title = self._book('EditBook', book, callback)  # Enter new title
        print(mb_title)
        if mb_title:
            if not mb_title[0].startswith('Enter new title'):
                return mb_title[0]
        self.process.write(new_info['title'])

        # year = self.process.read()  # Enter publication year
        _ = self._wait_strings(0.1)
        self.process.write(new_info['year'])
        # tags = self.process.read()  # Enter tags
        _ = self._wait_strings(0.1)
        self.process.write(new_info['tags'])

        if self._wait_select():
            return self.process.read()

    def add_book(self, year: int, title: str, author_or_callback: Union[str, Callable], tags: str, add_author_answer: str = 'y') -> Optional[str]:
        self.process.write(f'AddBook {year} {title}')
        if self._wait_select():
            _ = self.process.read()  # Enter author

        if isinstance(author_or_callback, str):
            self.process.write(author_or_callback)
            if self._wait_select():
                _ = self.process.read()  # y/n?
                self.process.write(add_author_answer)
        else:
            self.process.write('')
            authors = self._wait_strings()[1:-1]
            if authors:
                number, self.chose = author_or_callback(authors)
                self.process.write(f'{number}')
            else:
                self.process.write('')

        if self._wait_select():
            _ = self.process.read()   # Add tags
            self.process.write(tags)

        if self._wait_select():
            return self.process.read()

    def show_author_books(self, author_chooser: Optional[Callable] = None) -> List[str]:
        if author_chooser is None:
            author_chooser = Bookypedia.random_chooser
        self.process.write('ShowAuthorBooks')
        authors = self._wait_strings()[1:-1]
        if authors:
            number, self.chose = author_chooser(authors)
            self.process.write(f'{number}')
        else:
            self.process.write('')
        return self._wait_strings()

    def show_books(self) -> List[str]:
        self.process.write('ShowBooks')
        return self._wait_strings()


# @pytest.fixture(scope='function', params=['empty_db', 'table_db', 'full_db'])
# def bookypedia(request):
#     with run_bookypedia(request.param) as result:
#         yield result


@contextmanager
def run_bookypedia(db_name, terminate=True, reset_db=True):
    def _read(self):
        return self.stdout.readline().strip()

    def _write(self, message: str):
        self.stdin.write(f"{message.strip()}\n")
        self.stdin.flush()

    def _terminate(self):
        self.stdin.close()
        self.terminate()
        self.wait()

    try:
        if reset_db:
            drop_db(db_name)
            create_db(db_name)
    except Exception:
        pass

    db_connect = f"postgres://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{db_name}"
    proc = subprocess.Popen(os.environ['DELIVERY_APP'].split(), text=True, env=dict(os.environ, BOOKYPEDIA_DB_URL=db_connect),
                            stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    os.set_blocking(proc.stdout.fileno(), False)
    proc.write = types.MethodType(_write, proc)
    proc.read = types.MethodType(_read, proc)
    proc.new_terminate = types.MethodType(_terminate, proc)

    try:
        yield Bookypedia(proc, db_name)
    finally:
        if terminate:
            proc.new_terminate()


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_add_author(db_name):
    with run_bookypedia(db_name) as bookypedia:
        if db_name != 'full_db':
            assert bookypedia.add_author(None).startswith('Failed to add author')
            assert bookypedia.add_author('author2') is None
            assert bookypedia.add_author('author1') is None
            assert bookypedia.add_author('author2').startswith('Failed to add author')
        else:
            assert bookypedia.add_author(None).startswith('Failed to add author')
            assert bookypedia.add_author('author2').startswith('Failed to add author')
            assert bookypedia.add_author('author1').startswith('Failed to add author')
            assert bookypedia.add_author('author2').startswith('Failed to add author')


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_show_authors(db_name):
    with run_bookypedia(db_name) as bookypedia:
        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))

        bookypedia.add_author('author3')
        bookypedia.add_author('author2')
        bookypedia.add_author('author1')

        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_delete_existing_author_by_name(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        # without books
        extra_authors = [create_new_name(db_name) for _ in range(0, 3)]

        for author in extra_authors:
            assert bookypedia.add_author(author) is None
        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))

        for author in extra_authors:
            assert bookypedia.delete_author(author) is None

        for author in get_authors(db_name):
            assert bookypedia.delete_author(author[1]) is None  # Fails fot authors with books

        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))


# @pytest.mark.skip
@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_delete_existing_author_by_index(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        # without books
        extra_authors = [create_new_name(db_name) for _ in range(0, 3)]

        for author in extra_authors:
            assert bookypedia.add_author(author) is None
        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))

        for _ in get_authors(db_name):
            assert bookypedia.delete_author(bookypedia.random_chooser) is None  # Fails fot authors with books

        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_delete_author_canceling(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        # without books
        extra_authors = [create_new_name(db_name) for _ in range(0, 3)]

        for author in extra_authors:
            assert bookypedia.add_author(author) is None
        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))

        for _ in extra_authors:
            assert bookypedia.delete_author(bookypedia.empty_chooser) is None    # Returns Failed to delete author

        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_delete_non_existing_author(db_name):
    with run_bookypedia(db_name, reset_db=True) as bookypedia:
        bookypedia: Bookypedia

        non_existing_authors = [create_new_name(db_name) for _ in range(0, 3)]

        for pseudo_author in non_existing_authors:
            assert bookypedia.delete_author(pseudo_author).startswith('Failed to delete author')

        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_edit_author_by_name(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        # without books
        extra_authors = [create_new_name(db_name) for _ in range(0, 3)]

        for author in extra_authors:
            assert bookypedia.add_author(author) is None
        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))

        for author in [pair[1] for pair in get_authors(db_name)]:
            if db_name != 'empty_db':
                index = bookypedia.get_index_by_author(db_name, author)
                books = bookypedia.show_author_books(bookypedia.index_chooser(index))

            new_name: str = create_new_name(db_name)
            assert bookypedia.edit_author(author, new_name) is None
            if db_name != 'empty_db':
                index = bookypedia.get_index_by_author(db_name, new_name)
                print(index)
                assert books == bookypedia.show_author_books(bookypedia.index_chooser(index))

        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_edit_author_by_index(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        # without books
        extra_authors = [create_new_name(db_name) for _ in range(0, 3)]

        for author in extra_authors:
            assert bookypedia.add_author(author) is None
        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))

        authors = [pair[1] for pair in get_authors(db_name)]
        for author in authors:
            index = bookypedia.get_index_by_author(db_name, author)

            if db_name != 'empty_db':
                books = bookypedia.show_author_books(bookypedia.index_chooser(index - 1))

            new_name: str = create_new_name(db_name)
            assert bookypedia.edit_author(bookypedia.index_chooser(index - 1), new_name) is None
            if db_name != 'empty_db':
                index = bookypedia.get_index_by_author(db_name, new_name)
                assert books == bookypedia.show_author_books(bookypedia.index_chooser(index - 1))

        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_edit_author_canceling(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        # without books
        extra_authors = [create_new_name(db_name) for _ in range(0, 3)]

        for author in extra_authors:
            assert bookypedia.add_author(author) is None
        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))

        authors = [pair[1] for pair in get_authors(db_name)]
        for author in authors:
            index = bookypedia.get_index_by_author(db_name, author)

            if db_name != 'empty_db':
                books = bookypedia.show_author_books(bookypedia.index_chooser(index - 1))

            new_name: str = author
            assert bookypedia.edit_author(bookypedia.empty_chooser, None) is None
            if db_name != 'empty_db':
                index = bookypedia.get_index_by_author(db_name, new_name)
                assert books == bookypedia.show_author_books(bookypedia.index_chooser(index - 1))

        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_edit_non_existing_author(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        # without books
        extra_authors = [create_new_name(db_name) for _ in range(0, 3)]

        for author in extra_authors:
            assert bookypedia.add_author(author) is None
        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))

        new_name: str = create_new_name(db_name)
        res = bookypedia.edit_author(new_name, new_name)
        print(res)
        assert res.startswith('Failed to edit author')

        assert bookypedia.show_authors() == authors_to_str(get_authors(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_show_books(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        bookypedia.add_book(1563, 'How to cook an egg', bookypedia.random_chooser, 'tag23, tag14, tag 55')
        bookypedia.add_book(8763, 'Great man cannot do great things!', create_new_name(db_name), 'y')

        bookypedia.add_book(74, 'Strange ancient book!', create_new_name(db_name), 'tag1, tag2, tag3', 'y')

        books = bookypedia.show_books()
        db_books = books_to_str(get_books(db_name))

        assert books == db_books


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_show_book(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        books = [
            'How to cook an egg', 'Great man cannot do great things!', 'Strange ancient book!'
        ]
        for book in books:
            bookypedia.add_book(random.randint(1, 2054), book, create_new_name(db_name), create_messy_tags(15))

        for title in books:
            db_book = book_to_str(get_book(db_name, title)[0])

            bookypedia_book = bookypedia.show_book(title)
            assert db_book == bookypedia_book


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_show_book_choose_book(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        book_title = 'A new way to cook eggs!'
        authors = [create_new_name(db_name) for _ in range(3)]

        for author in authors:
            bookypedia.add_book(random.randint(1, 2054), book_title, author, create_messy_tags(15))

        for author in authors:

            db_books = get_book(db_name, book_title)
            for book in db_books:
                if book[2] == author:
                    break
            else:
                book = None
            book = book_to_str(book)
            bookypedia_book = bookypedia.show_book(book_title, bookypedia.book_chooser(author))
            assert bookypedia_book == book


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_show_book_by_global_index(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        books = [
            'How to cook an egg', 'Great man cannot do great things!', 'Strange ancient book!'
        ]
        for book in books:
            bookypedia.add_book(random.randint(1, 2054), book, create_new_name(db_name), create_messy_tags(15))
        db_books = get_books(db_name)
        string_books = bookypedia.show_books()
        print(string_books)
        for i, book in enumerate(string_books):
            for b in db_books:
                if book.find(b[1] + ' by') != -1:
                    title = b[1]
                    break
            print(title, book)
            db_dict_book = get_book(db_name, title)[0]
            print(db_dict_book)
            db_book = book_to_str(db_dict_book)
            print(db_book)
            bookypedia_book = bookypedia.show_book(callback=bookypedia.index_chooser(i))
            print(bookypedia_book)
            print(bookypedia_book)
            assert bookypedia_book == db_book


@pytest.mark.skip
@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_show_non_existing_book(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        books = [
            'How to cook an egg', 'Great man cannot do great things!', 'Strange ancient book!'
        ]

        for title in books:
            res = bookypedia.show_book(title)
            print(res)
            assert res[0].startswith('Book not found')


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_show_book_canceling(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        book_title = 'A new way to cook eggs!'
        authors = [create_new_name(db_name) for _ in range(3)]

        for author in authors:
            bookypedia.add_book(random.randint(1, 2054), book_title, author, create_messy_tags(15))
        authors.sort()

        for _ in authors:
            assert bookypedia.show_book(book_title, bookypedia.empty_chooser) == []
        for _ in authors:
            assert bookypedia.show_book(callback=bookypedia.empty_chooser) == []


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_delete_book(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        book_titles = [
            'How to cook an egg', 'Great man cannot do great things!', 'Strange ancient book!'
        ]
        for book in book_titles:
            bookypedia.add_book(random.randint(1, 2054), book, create_new_name(db_name), create_messy_tags(15))

        books = get_books(db_name)

        for book in books:
            title = book[1]
            author = book[3]
            assert bookypedia.delete_book(title) == []
            assert books_to_str(get_books(db_name)) == bookypedia.show_books()


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_delete_book_choose_book(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        book_title = 'A new way to cook eggs!'
        authors = [create_new_name(db_name) for _ in range(3)]

        for author in authors:
            bookypedia.add_book(random.randint(1, 2054), book_title, author, create_messy_tags(15))

        books = get_books(db_name)
        for book in books:
            title = book[1]
            author = book[3]
            assert bookypedia.delete_book(title, bookypedia.book_chooser(author)) == []
            assert books_to_str(get_books(db_name)) == bookypedia.show_books()


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_delete_book_by_global_index(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        books = [
            'How to cook an egg', 'Great man cannot do great things!', 'Strange ancient book!'
        ]
        for book in books:
            bookypedia.add_book(random.randint(1, 2054), book, create_new_name(db_name), create_messy_tags(15))
        for i, book in enumerate(get_books(db_name)):
            print(i, books_to_str(get_books(db_name)))
            bookypedia.delete_book(callback=bookypedia.index_chooser(0))

            assert bookypedia.show_books() == books_to_str(get_books(db_name))


@pytest.mark.skip
@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_delete_non_existing_book(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        book_titles = [
            'How to cook an egg', 'Great man cannot do great things!', 'Strange ancient book!'
        ]

        for title in book_titles:
            res = bookypedia.delete_book(title)
            print(res)
            assert res[0].startswith('Book not found')



@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_delete_book_canceling(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        book_title = 'A new way to cook eggs!'
        authors = [create_new_name(db_name) for _ in range(3)]

        for author in authors:
            bookypedia.add_book(random.randint(1, 2054), book_title, author, create_messy_tags(15))
        authors.sort()

        for _ in authors:
            assert bookypedia.delete_book(book_title, bookypedia.empty_chooser) == []
        for _ in authors:
            assert bookypedia.delete_book(callback=bookypedia.empty_chooser) == []


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_edit_book_by_name(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        books = [
            'How to cook an egg', 'Great man cannot do great things!', 'Strange ancient book!'
        ]
        for book in books:
            bookypedia.add_book(random.randint(1, 2054), book, create_new_name(db_name), create_messy_tags(15))
        books = get_books(db_name)
        for book in books:
            db_book = book_to_str(get_book(db_name, book[1])[0])
            bookypedia_book = bookypedia.show_book(book[1])
            assert db_book == bookypedia_book

            new_author = create_new_name(db_name)
            new_title = f'Biography of {new_author}'
            new_tags = create_messy_tags()
            new_year = random.randint(1, 6531)
            new_info = {
                'title': new_title,
                'year': str(new_year),
                'tags': new_tags
            }
            bookypedia.edit_book(book=book[1], new_info=new_info)

            db_book = book_to_str(get_book(db_name, new_title)[0])
            bookypedia_book = bookypedia.show_book(new_title)
            assert bookypedia_book == db_book
        assert bookypedia.show_books() == books_to_str(get_books(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_edit_book_choose_book(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        book_title = 'A new way to cook eggs!'
        authors = [create_new_name(db_name) for _ in range(3)]

        for author in authors:
            bookypedia.add_book(random.randint(1, 2054), book_title, author, create_messy_tags(15))

        chosen_author = random.choice(authors)

        db_books = get_book(db_name, book_title)
        for db_book in db_books:
            if db_book[2] == chosen_author:
                break
        else:
            db_book = None  # Something went wrong and an exceptions will be raised soon

        bookypedia_book = bookypedia.show_book(book_title, bookypedia.book_chooser(chosen_author))
        assert bookypedia_book == book_to_str(db_book)

        new_title = f'Biography of {author}'
        new_tags = create_messy_tags()
        new_year = random.randint(1, 6531)
        new_info = {
            'title': new_title,
            'year': str(new_year),
            'tags': new_tags
        }

        bookypedia.edit_book(book_title, bookypedia.book_chooser(chosen_author), new_info)
        time.sleep(5)

        db_book = book_to_str(get_book(db_name, new_title)[0])
        bookypedia_book = bookypedia.show_book(new_title)
        assert bookypedia_book == db_book
        assert bookypedia.show_books() == books_to_str(get_books(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_edit_book_by_global_index(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        books = [
            'How to cook an egg', 'Great man cannot do great things!', 'Strange ancient book!'
        ]
        for book in books:
            bookypedia.add_book(random.randint(1, 2054), book, create_new_name(db_name), create_messy_tags(15))
        db_books = get_books(db_name)
        string_books = bookypedia.show_books()
        print(string_books)

        book = random.choice(db_books)
        title = book[1]
        for i, book_string in enumerate(string_books):
            if book_string.find(title + ' by') == -1:
                continue

            bookypedia_book = bookypedia.show_book(title)
            assert bookypedia_book == book_to_str(get_book(db_name, title)[0])

            new_title = f'Biography of somebody'
            new_tags = create_messy_tags()
            new_year = random.randint(1, 6531)
            new_info = {
                'title': new_title,
                'year': str(new_year),
                'tags': new_tags
            }

            bookypedia.edit_book(callback=bookypedia.index_chooser(i), new_info=new_info)

            db_book = book_to_str(get_book(db_name, new_title)[0])
            bookypedia_book = bookypedia.show_book(new_title)
            assert bookypedia_book == db_book
            assert bookypedia.show_books() == books_to_str(get_books(db_name))


@pytest.mark.skip
@pytest.mark.parametrize('new_title', [False])
@pytest.mark.parametrize('new_year', [True, False])
@pytest.mark.parametrize('new_tags', [True, False])
@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_edit_book_empty_info(db_name, new_title, new_year, new_tags):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        books = [
            'How to cook an egg', 'Great man cannot do great things!', 'Strange ancient book!'
        ]
        for book in books:
            bookypedia.add_book(random.randint(1, 2054), book, create_new_name(db_name), create_messy_tags(15))
        db_books = get_books(db_name)
        string_books = bookypedia.show_books()
        print(string_books)

        book = random.choice(db_books)
        title = book[1]
        print(title, book)
        for i, book_string in enumerate(string_books):
            if book_string.find(title + ' by') == -1:
                continue
            db_book = book_to_str(get_book(db_name, title)[0])
            bookypedia_book = bookypedia.show_book(title)

            assert bookypedia_book == db_book

            new_book_title = 'Biography of someone' if new_title else ''

            new_info = {
                'title': new_book_title,
                'year': str(random.randint(1, 6531)) if new_year else '',
                'tags': create_messy_tags() if new_tags else ''
            }

            # if new_title:
            #     title = new_book_title
            # new_title = new_book_title if new_title else title
            bookypedia.edit_book(callback=bookypedia.index_chooser(i), new_info=new_info)
            print(title, new_title, new_book_title)
            print(get_books(db_name))
            time.sleep(5)
            if new_title:
                new_db_book = book_to_str(get_book(db_name, new_book_title)[0])
                new_bookypedia_book = bookypedia.show_book(new_book_title)

            else:
                new_db_book = book_to_str(get_book(db_name, title)[0])
                new_bookypedia_book = bookypedia.show_book(title)

            assert new_bookypedia_book == new_db_book
            assert bookypedia.show_books() == books_to_str(get_books(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_edit_non_existing_book(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        books = [
            'How to cook an egg', 'Great man cannot do great things!', 'Strange ancient book!'
        ]

        for book in books:
            assert bookypedia.edit_book(book=book, new_info=None).startswith('Book not found')

        assert bookypedia.show_books() == books_to_str(get_books(db_name))


@pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
def test_edit_book_canceling(db_name):
    with run_bookypedia(db_name) as bookypedia:
        bookypedia: Bookypedia

        book_title = 'A new way to cook eggs!'
        authors = [create_new_name(db_name) for _ in range(3)]

        for author in authors:
            bookypedia.add_book(random.randint(1, 2054), book_title, author, create_messy_tags(15))

        assert bookypedia.edit_book(callback=bookypedia.empty_chooser, new_info=None) is None

        assert bookypedia.show_books() == books_to_str(get_books(db_name))

        assert bookypedia.edit_book(book_title, callback=bookypedia.empty_chooser, new_info=None) is None

        assert bookypedia.show_books() == books_to_str(get_books(db_name))


# @pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
# def test_add_book(db_name):
#     with run_bookypedia(db_name) as bookypedia:
#         bookypedia.add_author('author3')
#         bookypedia.add_author('author2')
#         bookypedia.add_author('author1')
#
#         assert bookypedia.add_book(1111, 'Book1') is None
#         assert bookypedia.add_book(222, 'Book2') is None
#         assert bookypedia.add_book(33, 'Book3') is None


# @pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
# def test_show_author_books(db_name):
#     with run_bookypedia(db_name) as bookypedia:
#         bookypedia.show_books()
#         authors = get_authors(db_name)
#         for i in range(len(authors)):
#             books = bookypedia.show_author_books(Bookypedia.index_chooser(i))
#             assert books == get_author_books(db_name, authors[i]['id'])
#
#         bookypedia.add_author('author3')
#         bookypedia.add_author('author2')
#         bookypedia.add_author('author1')
#
#         bookypedia.add_book(1111, 'Title1', Bookypedia.index_chooser(0))
#         bookypedia.add_book(222, 'Title2', Bookypedia.index_chooser(0))
#         bookypedia.add_book(33, 'Title3', Bookypedia.index_chooser(1))
#
#         authors = get_authors(db_name)
#         for i in range(len(authors)):
#             books = bookypedia.show_author_books(Bookypedia.index_chooser(i))
#             assert books == get_author_books(db_name, authors[i]['id'])


# @pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
# def test_show_books(db_name):
#     with run_bookypedia(db_name) as bookypedia:
#         assert bookypedia.show_books() == books_to_str(get_books(db_name))
#
#         bookypedia.add_author('author3')
#         bookypedia.add_author('author2')
#         bookypedia.add_author('author1')
#
#         bookypedia.add_book(1111, 'Book1')
#         bookypedia.add_book(222, 'Book2')
#         bookypedia.add_book(33, 'Book3')
#
#         assert bookypedia.show_books() == books_to_str(get_books(db_name))
#
#
# @pytest.mark.parametrize('db_name', ['empty_db', 'table_db', 'full_db'])
# def test_concurrency(db_name):
#     with run_bookypedia(db_name) as bookypedia1:
#         time.sleep(0.2)
#         with run_bookypedia(db_name, reset_db=False) as bookypedia2:
#             books = books_to_str(get_books(db_name))
#             assert bookypedia1.show_books() == books
#             assert bookypedia2.show_books() == books
#
#             bookypedia1.add_author('AAAA')  # insert to top on list
#
#             def create_chooser(index: int):
#                 def chooser(authors):
#                     bookypedia2.add_author('A')  # insert to top on list
#                     time.sleep(0.2)
#                     return index+1, authors[index]
#                 return chooser
#
#             bookypedia1.add_book(2022, '!Title', create_chooser(0))
#
#             authors = get_authors(db_name)
#             for i, author in enumerate(authors):
#                 if author['name'] == 'AAAA':
#                     books = bookypedia1.show_author_books(Bookypedia.index_chooser(i))
#                     assert books == ['1 !Title, 2022']
#                 if author['name'] == 'A':
#                     books = bookypedia1.show_author_books(Bookypedia.index_chooser(i))
#                     assert books == []


def drop_db(db_name):
    conn = get_connection(None)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        try:
            cur.execute(f'drop database if exists {db_name};')
        except Exception as e:
            print(e)
    conn.close()


def create_db(db_name):
    conn = get_connection(None)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        cur.execute(f'create database {db_name};')
    conn.close()

    if db_name in {'table_db', 'full_db'}:
        with get_connection(db_name) as conn:
            with conn.cursor() as cur:
                # FIXME: Аналогично, заменить book tags на tags в решении

                cur.execute(
                    """CREATE TABLE IF NOT EXISTS authors (
                        id UUID CONSTRAINT firstindex PRIMARY KEY,
                        name varchar(100) NOT NULL UNIQUE
                    );
                    CREATE TABLE IF NOT EXISTS books (
                        id UUID PRIMARY KEY,
                        title VARCHAR(100) NOT NULL,
                        publication_year INT,
                        author_id UUID,
                        CONSTRAINT fk_authors
                            FOREIGN KEY(author_id)
                            REFERENCES authors(id)
                    );
                    CREATE TABLE IF NOT EXISTS book_tags (
                        book_id UUID,
                        tag varchar(30) NOT NULL,
                        CONSTRAINT fk_books
                            FOREIGN KEY(book_id)
                            REFERENCES books(id)
                    );
                    """)

    insert_author = f'INSERT INTO authors (id, name) VALUES (%s, %s);'
    insert_book = f'INSERT INTO books (id, title, author_id, publication_year) VALUES (%s, %s, %s, %s);'
    # FIXME: Аналогично, заменить book tags на tags в решении
    insert_tag = f'INSERT INTO book_tags (book_id, tag) VALUES (%s, %s);'
    if db_name == 'full_db':
        with get_connection(db_name) as conn:
            with conn.cursor() as cur:

                author_ids = []
                for i in range(5):
                    _uuid = uuid.uuid4().hex
                    author_ids.append(_uuid)
                    cur.execute(insert_author, (_uuid, f'author{i}'))

                for i in range(20):
                    book_id = uuid.uuid4().hex
                    cur.execute(insert_book, (book_id, f'Title{i}', random.choice(author_ids), 1000+i))
                    for j in range(random.randint(1, 4)):
                        # Requires at least one
                        # At least because otherwise get_book won't find such book ))
                        cur.execute(insert_tag, (book_id, f'tag{j}'))


if __name__ == '__main__':
    for name in ['empty_db', 'table_db', 'full_db']:
        drop_db(name)
        create_db(name)

    os.environ['POSTGRES_USER'] = 'postgres'
    os.environ['POSTGRES_PASSWORD'] = 'sdasd'
    os.environ['POSTGRES_HOST'] = '172.17.0.2'
    os.environ['POSTGRES_PORT'] = '5432'
