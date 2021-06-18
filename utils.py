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


def get_text_with_items(items):
    """ Преобразуем товары исходя из информации о них в текстовые сообщения
        Возвращаем список этих сообщений
    """
    items_text = []
    for item_id, article, item_size, item_name, url, existence, user_price in items:
        if existence:
            # размеры могут иметь буквенное обозначение, поэтому поле в БД TEXT
            # Приходится отсеивать товары без размера, сравнивая со строкой
            if item_size != '0':
                items_text.append(
                    "Отслеживание цены:\n"
                    f"[{item_name}]({url})\n"
                    f"Артикул: {article}\n"
                    f"Размер: {item_size}\n"
                    f"Ожидаемая цена: {user_price}\n"
                    f"ID товара: {item_id}\n"
                )
                continue
            items_text.append(
                "Отслеживание цены:\n"
                f"[{item_name}]({url})\n"
                f"Артикул: {article}\n"
                f"Ожидаемая цена: {user_price}\n"
                f"ID товара: {item_id}\n"
            )
            continue
        # размеры могут иметь буквенное обозначение, поэтому поле в БД TEXT
        # Приходится отсеивать товары без размера, сравнивая со строкой
        if item_size != '0':
            items_text.append(
                "Отслеживание появления:\n"
                f"[{item_name}]({url})\n"
                f"Артикул: {article}\n"
                f"Размер: {item_size}\n"
                f"ID товара: {item_id}\n"
            )
            continue
        items_text.append(
            "Отслеживание появления:\n"
            f"[{item_name}]({url})\n"
            f"Артикул: {article}\n"
            f"ID товара: {item_id}\n"
        )
        continue
    return items_text
