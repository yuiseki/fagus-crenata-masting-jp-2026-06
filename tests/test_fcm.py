import fcm
import pytest


def test_na_is_null_for_every_kind():
    assert fcm.value("Obs.seed.rnk.1999", "NA") is None
    assert fcm.value("Mean", "NA") is None


def test_kinds_follow_column_names():
    assert fcm.kind("Obs.seed.rnk.1999") == "int"
    assert fcm.kind("T.HSM.1999") == "float"
    assert fcm.kind("Site name in Japanese") == "text"
    assert fcm.kind("Altitude") == "int"


def test_unparseable_cell_fails():
    with pytest.raises(ValueError):
        fcm.value("Mean", "n/a")


def test_minus_one_rank_is_kept_as_published():
    assert fcm.value("Obs.seed.rnk.1999", "-1") == -1


def test_read_csv_drops_the_bom(tmp_path):
    p = tmp_path / "a.csv"
    p.write_bytes("﻿ID,x\n1,2\n".encode())
    assert fcm.read_csv(p)[0] == ["ID", "x"]
