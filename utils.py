def get_size_from_user(value):
    size = ''
    for i in value:
        if i.isalpha():
            i = i.lower()
        size += i
    return size


def get_thing_sizes(block_sizes):
    sizes = {}
    for block in block_sizes:
        size = str(block.select('span'))
        s_value = size.replace('[<span>', '').replace('</span>]', '')
        # на случай если размеры у товара не предусмотрены
        if s_value == '0':
            return
        # делаем буквы в нижнем регистре, так же сделаем с
        # введенными пользователем, чтоб не зависеть от регистра
        value = ''
        for i in s_value:
            if i.isalpha():
                i = i.lower()
            value += i
        flag = True
        if 'disabled' in str(block):
            flag = False
        sizes[value] = flag
    return sizes
