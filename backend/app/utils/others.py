"""Other things"""

def remove_accents(text):
    """
    Remove VNM accents from a string
    Xóa dấu tiếng Việt và chuyển thành không dấu
    """
    if not text:
        return text

    letters_to_replace = {
        'ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬ': 'A',
        'áàảãạăắằẳẵặâấầẩẫậ': 'a',
        'ÉÈẺẼẸÊẾỀỂỄỆ': 'E',
        'éèẻẽẹêếềểễệ': 'e',
        'ÍÌỈĨỊ': 'I',
        'íìỉĩị': 'i',
        'ÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢ': 'O',
        'óòỏõọôốồổỗộơớờởỡợ': 'o',
        'ÚÙỦŨỤƯỨỪỬỮỰ': 'U',
        'úùủũụưứừửữự': 'u',
        'ÝỲỶỸỴ': 'Y',
        'ýỳỷỹỵ': 'y',
        'Đ': 'D',
        'đ': 'd'
    }

    for chars, base in letters_to_replace.items():
        for char in chars:
            text = text.replace(char, base)

    return text
