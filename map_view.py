from config import (
    ROWS, COLS, EXTRA_COLS, EXTRA_ROWS_TOP, DEFAULT_COLOR,
    FONT_FAMILY_REGULAR, BASE_FONT_SIZE_NUMBER,
    CELL_SIZE, CELL_SPACING
)

def set_cell_default(r, c, cell_data):
    """Устанавливает начальные значения для ячейки."""
    if (r, c) not in cell_data:
        is_outer_main_grid = (r in [0, 6] or c in [0, 6]) and (0 <= r < ROWS and 0 <= c < COLS)
        default_name = "Введите имя залы"
        default_number = "0000"
        default_color = DEFAULT_COLOR
        default_text_color = '#CCCCCC'
        default_text_color_name = '#CCCCCC'

        if is_outer_main_grid:
            default_name = ""
            # Логика нумерации для внешнего контура (примерная)
            if r == 6: num = c + 1
            elif c == 6: num = 7 + (6 - r)
            elif r == 0: num = 13 + (6 - c)
            else: num = 19 + r
            default_number = f"{num:04d}"

        cell_data[(r, c)] = {
            'color': default_color, 'name': default_name, 'number': default_number,
            'text_color': default_text_color, 'text_color_name': default_text_color_name,
            'font_size_num': BASE_FONT_SIZE_NUMBER,
            'font_size_name': 12,
            'font_family_num': FONT_FAMILY_REGULAR,
            'font_weight_num': 'bold',
            'font_family_name': FONT_FAMILY_REGULAR, 'font_weight_name': 'normal',
            'is_default_name': True, 'is_default_number': True,
            'font_slant_num': 'roman', 'font_underline_num': False, 'font_overstrike_num': False,
            'font_slant_name': 'roman', 'font_underline_name': False, 'font_overstrike_name': False,
            'description_text': '', 'signal_text': '', 'key_action_enabled': False,
        }
        
        if is_outer_main_grid:
            cell_data[(r, c)]['room_type'] = 'Зала внутреннего контура'
            cell_data[(r, c)]['color'] = '#666666'
            cell_data[(r, c)]['text_color'] = '#CCCCCC'
            cell_data[(r, c)]['text_color_name'] = '#CCCCCC'
            cell_data[(r, c)]['name'] = ""
            cell_data[(r, c)]['is_default_name'] = True
            cell_data[(r, c)]['description_text'] = "В зале находится таймер на 20 мин и экран, транслирующий вид на какой-то город. Нет никакого испытания, можно кратко описать, чем занимаются персонажи."
            cell_data[(r, c)]['signal_text'] = "Досточтимые рыцари! Вы находитесь в зале внутреннего контура. Двери залы откроются через 20 минут."
            
        elif c >= COLS: # X and Z columns
             cell_data[(r, c)]['room_type'] = 'Сгенерированная зала'
             # Special cases for bottom cells
             if r == 0: # Bottom cells
                 if c == COLS: # X bottom
                     cell_data[(r, c)]['room_type'] = 'Белая зала'
                     cell_data[(r, c)]['color'] = '#FFFFFF'
                     cell_data[(r, c)]['text_color'] = '#000000'
                     cell_data[(r, c)]['text_color_name'] = '#000000'
                     cell_data[(r, c)]['number'] = "1001"
                     cell_data[(r, c)]['name'] = "Точка нужной координаты"
                     cell_data[(r, c)]['font_weight_name'] = 'normal' # Changed to normal
                     cell_data[(r, c)]['description_text'] = "Играет торжественная музыка. В центре залы находится консоль, в которую можно ввести требуемое для исполнения желание. В комнате стоят конструкторы, они смотрят на героев, что-то делают."
                     cell_data[(r, c)]['signal_text'] = "Досточтимые рыцари! Ваш поход завершен. Вы находитесь в белой зале конструктора под номером 1001. Для окончания похода просканируйте вашу эмблему, введите желание, требуемое для исполнения, а затем нажмите кнопку ввода."
                 elif c == COLS + 1: # Z bottom
                     cell_data[(r, c)]['room_type'] = 'Транспортная зала'
                     cell_data[(r, c)]['color'] = '#ffc000'
                     cell_data[(r, c)]['text_color'] = '#000000'
                     cell_data[(r, c)]['text_color_name'] = '#000000'
                     cell_data[(r, c)]['number'] = "2761"
                     cell_data[(r, c)]['name'] = "Переход вертикального уровня"
                     cell_data[(r, c)]['font_weight_name'] = 'normal' # Changed to normal
                     cell_data[(r, c)]['description_text'] = "Двери залы открыты. В центре залы стоит кабина лифта, напоминающего лифт из дорого отеля начала 21-го века.\nС помощью лифта можно переместиться на Оранжевый или Фиолетовый уровень конструктора"
                     cell_data[(r, c)]['signal_text'] = "Досточтимые рыцари! Вы находитесь в транспортной зале Конструктора. Двери залы открыты. Вы можете использовать залу для перемещения между уровнями Конструктора."

def get_cell_layout():
    """Возвращает словарь с координатами и размерами всех ячеек."""
    layout = {}
    
    # Main Grid (7x7)
    # r=0 is bottom, r=6 is top
    for r in range(ROWS):
        for c in range(COLS):
            x = c * (CELL_SIZE + CELL_SPACING)
            y = r * (CELL_SIZE + CELL_SPACING)
            layout[(r, c)] = (x, y, CELL_SIZE, CELL_SIZE)

    # Extra Columns (X and Z)
    # They are to the right of the main grid
    start_x = COLS * (CELL_SIZE + CELL_SPACING) + 1.5 * CELL_SIZE
    
    # Bottom cells (r=0 for X/Z columns)
    y_bottom = 0
    for c_offset in range(EXTRA_COLS):
        c = COLS + c_offset
        x = start_x + c_offset * (CELL_SIZE + CELL_SPACING)
        layout[(0, c)] = (x, y_bottom, CELL_SIZE, CELL_SIZE)

    # Top cells (r=1..5 for X/Z columns)
    gap = CELL_SIZE
    start_y_top = y_bottom + CELL_SIZE + gap
    
    for r_offset in range(EXTRA_ROWS_TOP):
        r = r_offset + 1 # 1 to 5
        for c_offset in range(EXTRA_COLS):
            c = COLS + c_offset
            x = start_x + c_offset * (CELL_SIZE + CELL_SPACING)
            y = start_y_top + r_offset * (CELL_SIZE + CELL_SPACING)
            layout[(r, c)] = (x, y, CELL_SIZE, CELL_SIZE)

    return layout
