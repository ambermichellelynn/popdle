from app.routers.game import _score_guess


def test_all_correct():
    correct, present = _score_guess("SHREK", "SHREK")
    assert correct == [0, 1, 2, 3, 4]
    assert present == []


def test_all_absent():
    # BLIMP shares no letters at all with SHREK.
    correct, present = _score_guess("BLIMP", "SHREK")
    assert correct == []
    assert present == []


def test_present_but_wrong_position():
    # SHREK contains S, H, R, E, K — guess shuffles two of them
    correct, present = _score_guess("HSREK", "SHREK")
    assert correct == [2, 3, 4]
    assert present == [0, 1]


def test_duplicate_letter_in_guess_capped_by_answer_count():
    # CRYPT has exactly one T. A guess with three T's (and no other letters
    # in common) should only mark ONE of them present — the rest absent.
    correct, present = _score_guess("TOTTI", "CRYPT")
    assert correct == []
    assert present == [0]


def test_duplicate_letter_present_in_both_at_different_counts():
    # SPEED has two E's. ERASE has two E's, neither in the correct spot.
    correct, present = _score_guess("ERASE", "SPEED")
    assert correct == []
    # Both E's in the guess should be marked present since SPEED has two E's.
    assert 0 in present
    assert 4 in present


def test_correct_position_consumes_letter_before_present_pass():
    # MOANA (M-O-A-N-A) has two A's at positions 2 and 4. Guessing AAAAA
    # should mark those two positions correct; since no A's remain
    # unaccounted for, the rest must be absent, not present.
    correct, present = _score_guess("AAAAA", "MOANA")
    assert correct == [2, 4]
    assert present == []


def test_empty_strings():
    correct, present = _score_guess("", "")
    assert correct == []
    assert present == []
