from backend.app.services.generator_service import generate_short_code


def test_generate_short_code_length():
    code = generate_short_code(7)
    assert len(code) == 7
    assert code.isalnum()
