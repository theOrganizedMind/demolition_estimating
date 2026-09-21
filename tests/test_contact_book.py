from estimate_project.contact_book import ContactBook


def test_contact_book_initial_state():
    book = ContactBook()

    assert book.filtered_contacts == []
    assert book.FONT == "Times New Roman"
    assert book.FONT_SIZE == 13
    assert book.TITLE_FONT == "Arial"
    assert book.TITLE_FONT_SIZE == 16
