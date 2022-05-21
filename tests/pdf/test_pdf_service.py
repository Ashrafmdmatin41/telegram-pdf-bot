import os
from pathlib import Path
from typing import Callable, List, cast
from unittest.mock import MagicMock, call, patch

import pytest
from PyPDF2.utils import PdfReadError as PyPdfReadError

from pdf_bot.compare import CompareService
from pdf_bot.pdf import PdfReadError, PdfService
from pdf_bot.telegram import TelegramService


@pytest.fixture(name="telegram_service")
def fixture_telegram_service() -> TelegramService:
    return cast(TelegramService, MagicMock())


@pytest.fixture(name="pdf_service")
def fixture_pdf_service(telegram_service: TelegramService) -> CompareService:
    return PdfService(telegram_service)


def test_compare_pdfs(
    pdf_service: PdfService,
    telegram_service: TelegramService,
    document_ids_generator: Callable[[int], List[str]],
):
    doc_ids = document_ids_generator(2)
    with patch(
        "pdf_bot.pdf.pdf_service.pdf_diff"
    ) as pdf_diff, pdf_service.compare_pdfs(*doc_ids):
        assert pdf_diff.main.called
        calls = [call(doc_id) for doc_id in doc_ids]
        telegram_service.download_file.assert_has_calls(calls, any_order=True)


def test_add_watermark_to_pdf(
    pdf_service: PdfService,
    telegram_service: TelegramService,
    get_data_file: Callable[[str], Path],
    context_manager_side_effect: Callable[[str], MagicMock],
):
    telegram_service.download_file.side_effect = context_manager_side_effect
    src_file = get_data_file("base.pdf")
    wmk_file = get_data_file("watermark.pdf")
    expected_file = get_data_file("base_watermark.pdf")

    with pdf_service.add_watermark_to_pdf(src_file, wmk_file) as out_fn:
        assert os.path.getsize(out_fn) == os.path.getsize(expected_file)


def test_add_watermark_to_pdf_read_error(pdf_service: PdfService):
    file_id = "file_id"
    with patch("pdf_bot.pdf.pdf_service.PdfFileReader") as pdf_file_reader:
        pdf_file_reader.side_effect = PyPdfReadError()
        with pytest.raises(PdfReadError), pdf_service.add_watermark_to_pdf(
            file_id, file_id
        ):
            pass