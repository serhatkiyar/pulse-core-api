import pytest

from app.hesaplamalar import topla


@pytest.mark.parametrize("sayi1, sayi2, sonuc", [(3, 2, 5), (8, 10, 18), (40, 50, 90)])
def test_topla(sayi1, sayi2, sonuc):
    toplam = topla(sayi1, sayi2)
    assert toplam == sonuc
