import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from collections import defaultdict
import math
import os
from datetime import datetime, timedelta
import configparser
try:
    from tkcalendar import Calendar
except ImportError:
    Calendar = None  # Будет работать без календаря

# PDF libraries
try:
    from reportlab.lib.pagesizes import letter, A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("ReportLab not installed. PDF export will be disabled.")
    print("Install with: pip install reportlab")


# Добавьте к существующим импортам:
try:
    from reportlab.graphics import renderPDF
    from reportlab.graphics.shapes import Drawing, Line, Rect, String, Group
    from reportlab.graphics.charts.textlabels import Label
    from svglib.svglib import svg2rlg
    import svgwrite
    SVG_AVAILABLE = True
except ImportError:
    SVG_AVAILABLE = False
    print("svgwrite not installed. SVG export will be disabled.")
    print("Install with: pip install svgwrite svglib")


def load_data_directory():
    """Загрузить путь к директории data из config.ini"""
    config = configparser.ConfigParser()
    config_file = 'config.ini'
    
    if os.path.exists(config_file):
        config.read(config_file)
        # Читаем convert_data из config.ini
        data_path = config.get('PATHS', 'convert_data', fallback=r'C:\Users\dotignore\Documents\Python\examplaone_krakenSDR_web\data')
        # Преобразуем '/' на '\' для Windows
        data_path = data_path.replace('/', '\\')
        return data_path
    else:
        # Если config.ini не найден, используем путь по умолчанию
        return r'C:\Users\dotignore\Documents\Python\examplaone_krakenSDR_web\data'


class VectorExporter:
    """Class for exporting network visualization to vector formats"""
    
    def __init__(self, visualizer):
        self.visualizer = visualizer
        
    def export_to_svg(self, filename):
        """Export network visualization to SVG file"""
        try:
            # Получаем данные для отрисовки
            data_to_draw = self.visualizer.filtered_file_data if self.visualizer.filtered_file_data else self.visualizer.file_data
            data_to_draw = [data for idx, data in enumerate(data_to_draw) if idx in self.visualizer.selected_files]
            
            # Фильтруем файлы с "No data in date range" - исключаем файлы без соединений
            data_to_draw = [data for data in data_to_draw if data.get('connections') and len(data['connections']) > 0]
            
            if not data_to_draw:
                return False
            
            # Вычисляем размеры
            rows, cols = self.visualizer.calculate_grid_dimensions(len(data_to_draw))
            total_width = cols * (self.visualizer.cell_width + self.visualizer.cell_padding) + self.visualizer.cell_padding
            
            # Вычисляем высоту
            total_height = 0
            for row_idx in range(rows):
                max_height = 0
                for col_idx in range(cols):
                    file_idx = row_idx * cols + col_idx
                    if file_idx < len(data_to_draw):
                        data = data_to_draw[file_idx]
                        num_nodes = max(len(data['from_counts']), len(data['to_counts']))
                        cell_height = (self.visualizer.cell_top_margin + 
                                     num_nodes * (self.visualizer.node_height + self.visualizer.node_spacing) + 
                                     self.visualizer.cell_padding)
                        max_height = max(max_height, cell_height)
                total_height += max_height + self.visualizer.cell_padding
            
            # Создаем SVG документ
            dwg = svgwrite.Drawing(filename, size=(f'{total_width}px', f'{total_height}px'))
            dwg.viewbox(0, 0, total_width, total_height)
            
            # Добавляем белый фон
            dwg.add(dwg.rect((0, 0), (total_width, total_height), fill='white'))
            
            # Рисуем каждую сеть
            current_y = self.visualizer.cell_padding
            for row_idx in range(rows):
                current_x = self.visualizer.cell_padding
                row_height = 0
                
                for col_idx in range(cols):
                    file_idx = row_idx * cols + col_idx
                    if file_idx < len(data_to_draw):
                        data = data_to_draw[file_idx]
                        cell_height = self._draw_network_svg(dwg, data, current_x, current_y, file_idx)
                        row_height = max(row_height, cell_height)
                    
                    current_x += self.visualizer.cell_width + self.visualizer.cell_padding
                
                current_y += row_height + self.visualizer.cell_padding
            
            # Сохраняем файл
            dwg.save()
            return True
            
        except Exception as e:
            print(f"Error exporting to SVG: {e}")
            return False
    
    def _draw_network_svg(self, dwg, data, x_offset, y_offset, file_idx):
        """Draw single network in SVG"""
        # Параметры
        node_width = self.visualizer.node_width
        node_height = self.visualizer.node_height
        node_spacing = self.visualizer.node_spacing
        column_distance = self.visualizer.column_distance
        
        # Позиции колонок
        left_x = x_offset + 50
        right_x = left_x + column_distance
        
        # Рамка ячейки
        cell_height = self.visualizer.cell_top_margin + max(len(data['from_counts']), len(data['to_counts'])) * (node_height + node_spacing) + self.visualizer.cell_padding
        dwg.add(dwg.rect((x_offset, y_offset), (self.visualizer.cell_width, cell_height), 
                         fill='none', stroke='#cccccc', stroke_width=1))
        
        # Заголовок
        dwg.add(dwg.text(data['filename'], 
                         insert=(x_offset + self.visualizer.cell_width // 2, y_offset + 15),
                         text_anchor='middle', font_size='10px', font_weight='bold'))
        
        # Частота
        dwg.add(dwg.text(data['frequency'],
                         insert=(x_offset + self.visualizer.cell_width // 2, y_offset + 30),
                         text_anchor='middle', font_size='14px', font_weight='bold'))
        
        # Заголовки колонок
        dwg.add(dwg.text('FROM', 
                         insert=(left_x + node_width // 2, y_offset + 45),
                         text_anchor='middle', font_size='12px', font_weight='bold'))
        dwg.add(dwg.text('TO',
                         insert=(right_x + node_width // 2, y_offset + 45),
                         text_anchor='middle', font_size='12px', font_weight='bold'))
        
        if not data['connections']:
            dwg.add(dwg.text('No data in date range',
                            insert=(x_offset + self.visualizer.cell_width // 2, y_offset + 80),
                            text_anchor='middle', font_size='10px', fill='#999999'))
            return cell_height
        
        # Сортированные узлы
        from_nodes = sorted(data['from_counts'].keys(), 
                          key=lambda x: data['from_counts'][x], reverse=True)
        to_nodes = sorted(data['to_counts'].keys(),
                        key=lambda x: data['to_counts'][x], reverse=True)
        
        # Позиции узлов
        from_positions = {}
        to_positions = {}
        
        y = y_offset + 60
        for node in from_nodes:
            from_positions[node] = y
            y += node_height + node_spacing
        
        y = y_offset + 60
        for node in to_nodes:
            to_positions[node] = y
            y += node_height + node_spacing
        
        # Максимум для нормализации
        max_conn = max(data['connections'].values()) if data['connections'] else 1
        
        # Получаем выделенные узлы
        selected_from = self.visualizer.selected_items.get(file_idx, {}).get('from', set())
        selected_to = self.visualizer.selected_items.get(file_idx, {}).get('to', set())
        
        # Рисуем линии соединений
        for (from_node, to_node), count in data['connections'].items():
            if from_node in from_positions and to_node in to_positions:
                normalized = count / max_conn
                width = self.visualizer.min_line_width + normalized * (self.visualizer.max_line_width - self.visualizer.min_line_width)
                
                x1 = left_x + node_width
                y1 = from_positions[from_node] + node_height // 2
                x2 = right_x
                y2 = to_positions[to_node] + node_height // 2
                
                line_color = self.visualizer.highlight_line_color if (from_node in selected_from and to_node in selected_to) else self.visualizer.line_color
                
                dwg.add(dwg.line((x1, y1), (x2, y2), stroke=line_color, stroke_width=width))
        
        # Рисуем узлы FROM
        for node, y in from_positions.items():
            bg_color = self.visualizer.selected_bg if node in selected_from else self.visualizer.node_bg
            
            # Прямоугольник узла
            dwg.add(dwg.rect((left_x, y), (node_width, node_height),
                            fill=bg_color, stroke=self.visualizer.node_border, stroke_width=1))
            
            # Текст узла
            dwg.add(dwg.text(str(node).rjust(8),
                            insert=(left_x + node_width // 2, y + node_height // 2 + 3),
                            text_anchor='middle', font_family='monospace', font_size='9px'))
            
            # Счетчик
            dwg.add(dwg.text(f'[{data["from_counts"][node]}]',
                            insert=(left_x - 5, y + node_height // 2 + 3),
                            text_anchor='end', font_family='monospace', font_size='9px',
                            fill=self.visualizer.count_color))
        
        # Рисуем узлы TO
        for node, y in to_positions.items():
            bg_color = self.visualizer.selected_bg if node in selected_to else self.visualizer.node_bg
            
            # Прямоугольник узла
            dwg.add(dwg.rect((right_x, y), (node_width, node_height),
                            fill=bg_color, stroke=self.visualizer.node_border, stroke_width=1))
            
            # Текст узла
            dwg.add(dwg.text(str(node).rjust(8),
                            insert=(right_x + node_width // 2, y + node_height // 2 + 3),
                            text_anchor='middle', font_family='monospace', font_size='9px'))
            
            # Счетчик
            dwg.add(dwg.text(f'[{data["to_counts"][node]}]',
                            insert=(right_x + node_width + 5, y + node_height // 2 + 3),
                            text_anchor='start', font_family='monospace', font_size='9px',
                            fill=self.visualizer.count_color))
        
        return cell_height








class PDFExporter:
    """Class for exporting network data to PDF with vector graphics"""
    
    def __init__(self, visualizer):
        self.visualizer = visualizer
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom PDF styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.HexColor('#000080')
        ))
        
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#000080'),
            spaceBefore=20,
            spaceAfter=10
        ))
    
    def create_network_drawing(self, data, file_idx, page_width, page_height):
        """Create ReportLab drawing for single network - exactly 40 nodes"""
        from reportlab.graphics.shapes import Drawing, Line, Rect, String, Group
        
        # Используем всю доступную ширину страницы
        margin = 30
        available_width = page_width - (2 * margin)
        available_height = min(600, page_height - 150)  # Увеличиваем высоту для 40 узлов
        
        # Создаем Drawing
        drawing = Drawing(available_width, available_height)
        
        # Параметры визуализации
        node_width = 80
        node_height = 14  # Уменьшаем высоту узла чтобы поместилось 40
        node_spacing = 1   # Минимальный отступ
        column_distance = available_width - node_width - 100
        
        # Позиции колонок
        left_x = 50
        right_x = available_width - node_width - 50
        
        # Заголовки колонок
        drawing.add(String(left_x + node_width // 2, available_height - 20, 
                        'FROM', textAnchor='middle', fontSize=12, fontName='Helvetica-Bold'))
        drawing.add(String(right_x + node_width // 2, available_height - 20, 
                        'TO', textAnchor='middle', fontSize=12, fontName='Helvetica-Bold'))
        
        if not data['connections']:
            drawing.add(String(available_width // 2, available_height // 2, 
                            'No data in date range', 
                            textAnchor='middle', fontSize=10, fillColor=colors.grey))
            return drawing
        
        # РОВНО 40 узлов FROM и 40 узлов TO
        NODES_TO_SHOW = 40
        
        # Получаем топ-40 FROM узлов
        from_nodes = sorted(data['from_counts'].keys(), 
                        key=lambda x: data['from_counts'][x], reverse=True)[:NODES_TO_SHOW]
        
        # Получаем топ-40 TO узлов
        to_nodes = sorted(data['to_counts'].keys(),
                        key=lambda x: data['to_counts'][x], reverse=True)[:NODES_TO_SHOW]
        
        # Если узлов меньше 40, дополняем пустыми местами
        while len(from_nodes) < NODES_TO_SHOW and len(from_nodes) < len(data['from_counts']):
            from_nodes = list(data['from_counts'].keys())[:NODES_TO_SHOW]
            break
        
        while len(to_nodes) < NODES_TO_SHOW and len(to_nodes) < len(data['to_counts']):
            to_nodes = list(data['to_counts'].keys())[:NODES_TO_SHOW]
            break
        
        # Позиции узлов - размещаем ровно 40
        from_positions = {}
        to_positions = {}
        
        start_y = available_height - 40
        total_height_needed = NODES_TO_SHOW * (node_height + node_spacing)
        
        # Вычисляем начальную позицию чтобы узлы были по центру
        if total_height_needed < (available_height - 60):
            start_y = available_height - 40
        else:
            # Если не помещается, уменьшаем высоту узлов
            node_height = ((available_height - 60) / NODES_TO_SHOW) - node_spacing
            node_height = max(node_height, 10)  # Минимум 10 пикселей высота
        
        # Размещаем FROM узлы
        y = start_y
        for i, node in enumerate(from_nodes):
            if i >= NODES_TO_SHOW:  # Ограничиваем ровно 40
                break
            from_positions[node] = y
            y -= (node_height + node_spacing)
        
        # Размещаем TO узлы
        y = start_y
        for i, node in enumerate(to_nodes):
            if i >= NODES_TO_SHOW:  # Ограничиваем ровно 40
                break
            to_positions[node] = y
            y -= (node_height + node_spacing)
        
        # Максимум для нормализации
        max_conn = max(data['connections'].values()) if data['connections'] else 1
        
        # Получаем выделенные узлы
        selected_from = self.visualizer.selected_items.get(file_idx, {}).get('from', set())
        selected_to = self.visualizer.selected_items.get(file_idx, {}).get('to', set())
        
        # Показываем топ соединения между отображаемыми узлами
        connections_to_draw = []
        for (from_node, to_node), count in data['connections'].items():
            if from_node in from_positions and to_node in to_positions:
                connections_to_draw.append(((from_node, to_node), count))
        
        # Сортируем и берем топ-150
        connections_to_draw.sort(key=lambda x: x[1], reverse=True)
        connections_to_draw = connections_to_draw[:150]
        
        # Рисуем линии соединений
        for (from_node, to_node), count in connections_to_draw:
            normalized = count / max_conn
            line_width = 0.2 + normalized * 2.5
            
            x1 = left_x + node_width
            y1 = from_positions[from_node] - node_height // 2
            x2 = right_x
            y2 = to_positions[to_node] - node_height // 2
            
            if from_node in selected_from and to_node in selected_to:
                line_color = colors.red
                line_width = max(line_width, 1.5)
            else:
                line_color = colors.Color(0.7, 0.7, 0.7, alpha=0.4)
            
            drawing.add(Line(x1, y1, x2, y2, strokeColor=line_color, strokeWidth=line_width))
        
        # Рисуем FROM узлы
        for i, (node, y) in enumerate(from_positions.items()):
            if i >= NODES_TO_SHOW:
                break
                
            if node in selected_from:
                fill_color = colors.yellow
                stroke_width = 1
            else:
                fill_color = colors.Color(0.95, 0.95, 0.95)
                stroke_width = 0.5
            
            # Прямоугольник узла
            drawing.add(Rect(left_x, y - node_height, node_width, node_height,
                        fillColor=fill_color, strokeColor=colors.black, strokeWidth=stroke_width))
            
            # Текст узла
            node_str = str(node)[:10].rjust(8)
            font_size = min(8, node_height - 4)  # Адаптивный размер шрифта
            drawing.add(String(left_x + node_width // 2, y - node_height // 2 - 2,
                            node_str, textAnchor='middle', fontSize=font_size, fontName='Courier'))
            
            # Счетчик слева
            drawing.add(String(left_x - 5, y - node_height // 2 - 2,
                            f'[{data["from_counts"][node]}]',
                            textAnchor='end', fontSize=font_size, fontName='Helvetica',
                            fillColor=colors.grey))
        
        # Рисуем TO узлы
        for i, (node, y) in enumerate(to_positions.items()):
            if i >= NODES_TO_SHOW:
                break
                
            if node in selected_to:
                fill_color = colors.yellow
                stroke_width = 1
            else:
                fill_color = colors.Color(0.95, 0.95, 0.95)
                stroke_width = 0.5
            
            # Прямоугольник узла
            drawing.add(Rect(right_x, y - node_height, node_width, node_height,
                        fillColor=fill_color, strokeColor=colors.black, strokeWidth=stroke_width))
            
            # Текст узла
            node_str = str(node)[:10].rjust(8)
            font_size = min(8, node_height - 4)
            drawing.add(String(right_x + node_width // 2, y - node_height // 2 - 2,
                            node_str, textAnchor='middle', fontSize=font_size, fontName='Courier'))
            
            # Счетчик справа
            drawing.add(String(right_x + node_width + 5, y - node_height // 2 - 2,
                            f'[{data["to_counts"][node]}]',
                            textAnchor='start', fontSize=font_size, fontName='Helvetica',
                            fillColor=colors.grey))
        
        # Легенда - указываем ТОЧНОЕ количество
        actual_from_count = min(len(from_nodes), NODES_TO_SHOW)
        actual_to_count = min(len(to_nodes), NODES_TO_SHOW)
        
        legend_y = 10
        drawing.add(String(available_width // 2, legend_y,
                        f'Showing exactly {actual_from_count} FROM nodes, {actual_to_count} TO nodes, {len(connections_to_draw)} connections',
                        textAnchor='middle', fontSize=7, fillColor=colors.grey))
        
        return drawing
    

    
    def export_to_pdf(self, filename):
        """Export current view to PDF with vector graphics"""
        try:
            # Используем портретную ориентацию
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=50,
                leftMargin=50,
                topMargin=50,
                bottomMargin=30,
            )
            
            # Получаем размер страницы
            page_width, page_height = A4
            
            elements = []
            
            # Титульная страница
            title = Paragraph("DMR Network Connections Report", self.styles['CustomTitle'])
            elements.append(title)
            
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subtitle = Paragraph(f"Generated: {date_str}", self.styles['Subtitle'])
            elements.append(subtitle)
            
            elements.append(Spacer(1, 0.2*inch))
            
            # Информация о фильтрах
            elements.extend(self.get_filter_info())
            
            # Статистика
            elements.extend(self.get_statistics())
            
            # Выбираем данные для отрисовки
            data_source = self.visualizer.filtered_file_data if self.visualizer.filtered_file_data else self.visualizer.file_data
            data_to_draw = [data for idx, data in enumerate(data_source) if idx in self.visualizer.selected_files]
            
            # Визуализация для каждого файла
            for idx, data in enumerate(data_to_draw):
                elements.append(PageBreak())
                
                # Заголовок файла
                elements.append(Paragraph(f"Network Visualization: {data['filename']}", 
                                        self.styles['SectionHeader']))
                elements.append(Paragraph(f"Frequency: {data['frequency']}", 
                                        self.styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
                
                # Находим индекс файла
                file_idx = None
                for orig_idx in self.visualizer.selected_files:
                    if self.visualizer.file_data[orig_idx] == data or \
                    (self.visualizer.filtered_file_data and 
                        orig_idx < len(self.visualizer.filtered_file_data) and 
                        self.visualizer.filtered_file_data[orig_idx] == data):
                        file_idx = orig_idx
                        break
                
                if file_idx is not None:
                    drawing = self.create_network_drawing(data, file_idx, page_width, page_height)
                    elements.append(drawing)
                
                elements.append(Spacer(1, 0.1*inch))
                
                # ИЗМЕНЕНО: отображаем 40 узлов и 150 соединений
                elements.append(Paragraph(f"<i>Showing top 40 nodes and top 150 connections</i>", 
                                        self.styles['Normal']))
            
            # Детальные таблицы соединений
            elements.append(PageBreak())
            elements.append(Paragraph("Connection Details", self.styles['SectionHeader']))
            elements.extend(self.get_connection_tables())
            
            # Создаем PDF
            doc.build(elements)
            print(f"PDF saved successfully to: {filename}")
            return True
            
        except Exception as e:
            print(f"Error exporting to PDF: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_filter_info(self):
        """Get filter information for PDF"""
        elements = []
        
        elements.append(Paragraph("Applied Filters", self.styles['SectionHeader']))
        
        filter_data = []
        
        date_from = self.visualizer.date_from_var.get()
        date_to = self.visualizer.date_to_var.get()
        filter_data.append(["Date Range:", f"{date_from} to {date_to}"])
        
        if self.visualizer.duration_from_var.get() or self.visualizer.duration_to_var.get():
            dur_from = self.visualizer.duration_from_var.get() or "0"
            dur_to = self.visualizer.duration_to_var.get() or "∞"
            filter_data.append(["Duration:", f"{dur_from} - {dur_to} seconds"])
        
        if self.visualizer.selected_event.get() != 'All':
            filter_data.append(["Event:", self.visualizer.selected_event.get()])
        
        if self.visualizer.selected_timeslot.get() != 'All':
            filter_data.append(["Timeslot:", self.visualizer.selected_timeslot.get()])
        
        if self.visualizer.selected_color_code.get() != 'All':
            filter_data.append(["Color Code:", self.visualizer.selected_color_code.get()])
        
        if self.visualizer.selected_algorithm.get() != 'All':
            filter_data.append(["Algorithm:", self.visualizer.selected_algorithm.get()])
        
        if self.visualizer.selected_key.get() != 'All':
            filter_data.append(["Key:", self.visualizer.selected_key.get()])
        
        if filter_data:
            filter_table = Table(filter_data, colWidths=[1.5*inch, 4*inch])
            filter_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))
            elements.append(filter_table)
        
        elements.append(Spacer(1, 0.2*inch))
        return elements
    
    def get_statistics(self):
        """Get statistics for PDF"""
        elements = []
        
        elements.append(Paragraph("Statistics", self.styles['SectionHeader']))
        
        data_source = self.visualizer.filtered_file_data if self.visualizer.filtered_file_data else self.visualizer.file_data
        data_to_analyze = [data for idx, data in enumerate(data_source) if idx in self.visualizer.selected_files]
        
        stats_data = []
        total_connections = 0
        total_from_nodes = set()
        total_to_nodes = set()
        
        for data in data_to_analyze:
            file_connections = sum(data['connections'].values())
            total_connections += file_connections
            total_from_nodes.update(data['from_counts'].keys())
            total_to_nodes.update(data['to_counts'].keys())
            
            stats_data.append([
                os.path.basename(data['file_path'])[:20],
                data['frequency'],
                str(file_connections),
                str(len(data['from_counts'])),
                str(len(data['to_counts']))
            ])
        
        stats_data.append([
            "TOTAL",
            "",
            str(total_connections),
            str(len(total_from_nodes)),
            str(len(total_to_nodes))
        ])
        
        stats_table = Table(
            [["File", "Frequency", "Connections", "FROM", "TO"]] + stats_data,
            colWidths=[2*inch, 1.3*inch, 1*inch, 0.8*inch, 0.8*inch]
        )
        
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def get_connection_tables(self):
        """Get ALL connection tables with full page width"""
        elements = []
        
        data_source = self.visualizer.filtered_file_data if self.visualizer.filtered_file_data else self.visualizer.file_data
        data_to_export = [data for idx, data in enumerate(data_source) if idx in self.visualizer.selected_files]
        
        for data in data_to_export:
            if elements:
                elements.append(PageBreak())
            
            elements.append(Paragraph(f"All Connections: {data['filename']}", self.styles['SectionHeader']))
            elements.append(Paragraph(f"Frequency: {data['frequency']}", self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
            
            sorted_connections = sorted(data['connections'].items(), key=lambda x: x[1], reverse=True)
            
            if sorted_connections:
                elements.append(Paragraph(f"Total connections: {len(sorted_connections)}", self.styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
                
                rows_per_page = 60  # Увеличиваем количество строк на странице
                
                for page_num in range(0, len(sorted_connections), rows_per_page):
                    if page_num > 0:
                        elements.append(PageBreak())
                        elements.append(Paragraph(f"Connections: {data['filename']} (continued)", 
                                                self.styles['SectionHeader']))
                    
                    page_connections = sorted_connections[page_num:page_num + rows_per_page]
                    
                    connection_rows = []
                    for i, ((from_id, to_id), count) in enumerate(page_connections):
                        connection_rows.append([
                            str(page_num + i + 1),
                            str(from_id),
                            str(to_id),
                            str(count)
                        ])
                    
                    # Используем всю ширину страницы для таблицы
                    # A4 = 595 points width, с полями 50 points = 495 points доступно
                    available_width = 495
                    
                    header = ["#", "FROM", "TO", "Count"]
                    # Распределяем ширину колонок для максимального использования пространства
                    conn_table = Table([header] + connection_rows, 
                                    colWidths=[
                                        0.6*inch,      # № - узкая колонка
                                        3.2*inch,      # FROM - широкая колонка
                                        3.2*inch,      # TO - широкая колонка  
                                        0.8*inch       # Count - узкая колонка
                                    ])
                    
                    conn_table.setStyle(TableStyle([
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # № - по центру
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),    # FROM - слева
                        ('ALIGN', (2, 0), (2, -1), 'LEFT'),    # TO - слева
                        ('ALIGN', (3, 0), (3, -1), 'CENTER'),  # Count - по центру
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 1)]),
                        ('LEFTPADDING', (0, 0), (-1, -1), 3),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ]))
                    
                    elements.append(conn_table)
                    
                    # Номер страницы
                    page_info = f"Page {page_num // rows_per_page + 1} of {(len(sorted_connections) - 1) // rows_per_page + 1}"
                    elements.append(Spacer(1, 0.05*inch))
                    elements.append(Paragraph(f"<i>{page_info}</i>", self.styles['Normal']))
            
            else:
                no_data = Paragraph("<i>No connections in the selected date range</i>", self.styles['Normal'])
                elements.append(no_data)
            
            elements.append(Spacer(1, 0.1*inch))
        
        return elements















class DateMaskEntry(tk.Frame):
    """Widget for date input with mask DD/MM/YY HH:MM:SS and calendar"""
    def __init__(self, parent, textvariable=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.textvariable = textvariable
        
        # Frame for entry and button
        input_frame = tk.Frame(self)
        input_frame.pack(side=tk.LEFT)
        
        # Create Entry
        self.entry = tk.Entry(input_frame, width=17, font=("Courier", 9))
        self.entry.pack(side=tk.LEFT)
        
        # Calendar icon button
        self.cal_button = tk.Button(input_frame, text="📅", width=2, 
                                   command=self.show_calendar,
                                   font=("Arial", 10), cursor="hand2",
                                   relief=tk.FLAT, bg="#f5f5f5")
        self.cal_button.pack(side=tk.LEFT, padx=(2, 0))
        
        # Initial value
        self.entry.insert(0, "01/01/25 00:00:00")
        
        # Bind events
        self.entry.bind('<KeyPress>', self.on_key_press)
        self.entry.bind('<Left>', self.on_arrow_left)
        self.entry.bind('<Right>', self.on_arrow_right)
        
        # Separator positions
        self.separators = {2: '/', 5: '/', 8: ' ', 11: ':', 14: ':'}
        self.field_positions = [
            (0, 2),   # DD
            (3, 5),   # MM
            (6, 8),   # YY
            (9, 11),  # HH
            (12, 14), # MM
            (15, 17)  # SS
        ]
        
        # Synchronization with textvariable
        if self.textvariable:
            self.textvariable.trace('w', self.update_from_var)
            self.update_from_var()
    
    def on_arrow_left(self, event):
        """Handle left arrow key"""
        pos = self.entry.index(tk.INSERT)
        
        # Skip separators when moving left
        if pos > 0:
            pos -= 1
            if pos in self.separators:
                pos -= 1
            self.entry.icursor(pos)
        return 'break'
    
    def on_arrow_right(self, event):
        """Handle right arrow key"""
        pos = self.entry.index(tk.INSERT)
        
        # Skip separators when moving right
        if pos < 16:
            pos += 1
            if pos in self.separators:
                pos += 1
            self.entry.icursor(pos)
        return 'break'
    
    def on_key_press(self, event):
        """Handle key press events"""
        if event.char.isdigit():
            pos = self.entry.index(tk.INSERT)
            
            # Don't allow input at separator positions
            if pos in self.separators:
                return 'break'
            
            # Replace character at cursor position
            text = list(self.entry.get())
            if pos < len(text):
                text[pos] = event.char
                self.entry.delete(0, tk.END)
                self.entry.insert(0, ''.join(text))
                
                # Don't move cursor automatically, keep in place
                new_pos = pos + 1
                
                # Skip separator only if next position is a separator
                if new_pos in self.separators:
                    new_pos += 1
                    
                # Check if we're within bounds
                if new_pos <= 16:
                    self.entry.icursor(new_pos)
                else:
                    self.entry.icursor(pos)
            
            # Update variable
            if self.textvariable:
                self.textvariable.set(self.entry.get())
                
            return 'break'
        
        elif event.keysym == 'BackSpace':
            pos = self.entry.index(tk.INSERT)
            if pos > 0 and pos - 1 not in self.separators:
                text = list(self.entry.get())
                text[pos - 1] = '0'
                self.entry.delete(0, tk.END)
                self.entry.insert(0, ''.join(text))
                self.entry.icursor(pos - 1)
            return 'break'
        
        elif event.keysym in ['Tab', 'Return']:
            return  # Allow standard behavior
        
        return 'break'
    
    def show_calendar(self):
        """Show calendar for date and time selection"""
        if not Calendar:
            print("tkcalendar not installed! Install: pip install tkcalendar")
            return
            
        cal_window = tk.Toplevel(self)
        cal_window.title("Select date and time")
        # Increase window height to ensure buttons fit
        cal_window.geometry("320x520")
        cal_window.resizable(False, False)
        
        try:
            current_date_str = self.entry.get()
            current_date = datetime.strptime(current_date_str, "%d/%m/%y %H:%M:%S")
        except:
            current_date = datetime.now()
        
        # Main container with scrolling if needed
        main_container = tk.Frame(cal_window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Frame for calendar
        date_frame = tk.LabelFrame(main_container, text="Date", padx=10, pady=5)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        cal = Calendar(date_frame, selectmode='day',
                    year=current_date.year, 
                    month=current_date.month,
                    day=current_date.day,
                    date_pattern='dd/mm/yyyy')
        cal.pack()
        
        # Frame for time
        time_frame = tk.LabelFrame(main_container, text="Time (click to select)", padx=10, pady=5)
        time_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Variables for selected time
        selected_hour = tk.IntVar(value=current_date.hour)
        selected_min = tk.IntVar(value=current_date.minute)
        selected_sec = tk.IntVar(value=current_date.second)
        
        # Frame for displaying selected time
        selected_time_frame = tk.Frame(time_frame)
        selected_time_frame.pack(pady=5)
        
        hour_label = tk.Label(selected_time_frame, text=f"{selected_hour.get():02d}", 
                            font=("Courier", 16, "bold"), width=2, relief=tk.SUNKEN, bg="white")
        hour_label.grid(row=0, column=0, padx=2)
        
        tk.Label(selected_time_frame, text=":", font=("Courier", 16, "bold")).grid(row=0, column=1)
        
        min_label = tk.Label(selected_time_frame, text=f"{selected_min.get():02d}", 
                            font=("Courier", 16, "bold"), width=2, relief=tk.SUNKEN, bg="white")
        min_label.grid(row=0, column=2, padx=2)
        
        tk.Label(selected_time_frame, text=":", font=("Courier", 16, "bold")).grid(row=0, column=3)
        
        sec_label = tk.Label(selected_time_frame, text=f"{selected_sec.get():02d}", 
                            font=("Courier", 16, "bold"), width=2, relief=tk.SUNKEN, bg="white")
        sec_label.grid(row=0, column=4, padx=2)
        
        # Frame with three columns for time selection (reduce height)
        picker_frame = tk.Frame(time_frame)
        picker_frame.pack(fill=tk.X)
        
        # Hours column
        hour_frame = tk.Frame(picker_frame)
        hour_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(hour_frame, text="Hours", font=("Arial", 9)).pack()
        
        hour_listbox = tk.Listbox(hour_frame, height=4, width=4, font=("Courier", 10))
        hour_scroll = tk.Scrollbar(hour_frame, orient="vertical", command=hour_listbox.yview)
        hour_listbox.configure(yscrollcommand=hour_scroll.set)
        
        for i in range(24):
            hour_listbox.insert(tk.END, f"{i:02d}")
        
        hour_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        hour_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        hour_listbox.selection_set(current_date.hour)
        hour_listbox.see(current_date.hour)
        
        # Minutes column
        min_frame = tk.Frame(picker_frame)
        min_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(min_frame, text="Minutes", font=("Arial", 9)).pack()
        
        min_listbox = tk.Listbox(min_frame, height=4, width=4, font=("Courier", 10))
        min_scroll = tk.Scrollbar(min_frame, orient="vertical", command=min_listbox.yview)
        min_listbox.configure(yscrollcommand=min_scroll.set)
        
        for i in range(60):
            min_listbox.insert(tk.END, f"{i:02d}")
        
        min_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        min_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        min_listbox.selection_set(current_date.minute)
        min_listbox.see(current_date.minute)
        
        # Seconds column
        sec_frame = tk.Frame(picker_frame)
        sec_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(sec_frame, text="Seconds", font=("Arial", 9)).pack()
        
        sec_listbox = tk.Listbox(sec_frame, height=4, width=4, font=("Courier", 10))
        sec_scroll = tk.Scrollbar(sec_frame, orient="vertical", command=sec_listbox.yview)
        sec_listbox.configure(yscrollcommand=sec_scroll.set)
        
        for i in range(60):
            sec_listbox.insert(tk.END, f"{i:02d}")
        
        sec_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        sec_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        sec_listbox.selection_set(current_date.second)
        sec_listbox.see(current_date.second)
        
        # Update functions on selection
        def on_hour_select(event):
            selection = hour_listbox.curselection()
            if selection:
                selected_hour.set(selection[0])
                hour_label.config(text=f"{selection[0]:02d}")
        
        def on_min_select(event):
            selection = min_listbox.curselection()
            if selection:
                selected_min.set(selection[0])
                min_label.config(text=f"{selection[0]:02d}")
        
        def on_sec_select(event):
            selection = sec_listbox.curselection()
            if selection:
                selected_sec.set(selection[0])
                sec_label.config(text=f"{selection[0]:02d}")
        
        hour_listbox.bind('<<ListboxSelect>>', on_hour_select)
        min_listbox.bind('<<ListboxSelect>>', on_min_select)
        sec_listbox.bind('<<ListboxSelect>>', on_sec_select)
        
        # IMPORTANT: apply_datetime function must be defined BEFORE creating buttons
        def apply_datetime():
            date_str = cal.get_date()
            selected_date = datetime.strptime(date_str, '%d/%m/%Y')
            
            final_date = selected_date.replace(hour=selected_hour.get(), 
                                            minute=selected_min.get(), 
                                            second=selected_sec.get())
            date_formatted = final_date.strftime("%d/%m/%y %H:%M:%S")
            
            self.entry.delete(0, tk.END)
            self.entry.insert(0, date_formatted)
            
            if self.textvariable:
                self.textvariable.set(date_formatted)
            
            cal_window.destroy()
        
        # CONTROL BUTTONS - IMPORTANT PART!
        # Place buttons at the bottom of the window
        button_frame = tk.Frame(cal_window, bg="#e0e0e0", height=60)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        button_frame.pack_propagate(False)  # Fix height
        
        # Create buttons
        ok_button = tk.Button(button_frame, 
                            text="✓ APPLY", 
                            command=apply_datetime,
                            bg="#4CAF50", 
                            fg="white", 
                            font=("Arial", 11, "bold"),
                            width=12,
                            height=2,
                            cursor="hand2")
        ok_button.pack(side=tk.LEFT, padx=20, pady=10)
        
        cancel_button = tk.Button(button_frame, 
                                text="✗ CANCEL", 
                                command=cal_window.destroy,
                                bg="#f44336", 
                                fg="white", 
                                font=("Arial", 11, "bold"),
                                width=12,
                                height=2,
                                cursor="hand2")
        cancel_button.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Make window modal
        cal_window.transient(self.winfo_toplevel())
        cal_window.grab_set()
        
        # Center window
        cal_window.update_idletasks()
        x = (cal_window.winfo_screenwidth() // 2) - (160)
        y = (cal_window.winfo_screenheight() // 2) - (260)
        cal_window.geometry(f"+{x}+{y}")

    def set_current_time(self, hour_lb, min_lb, sec_lb, hour_l, min_l, sec_l, h_var, m_var, s_var):
        """Установить текущее время"""
        now = datetime.now()
        self.set_time(now.hour, now.minute, now.second, 
                    hour_lb, min_lb, sec_lb, hour_l, min_l, sec_l, h_var, m_var, s_var)

    def set_time(self, h, m, s, hour_lb, min_lb, sec_lb, hour_l, min_l, sec_l, h_var, m_var, s_var):
        """Установить конкретное время"""
        # Очищаем старое выделение
        hour_lb.selection_clear(0, tk.END)
        min_lb.selection_clear(0, tk.END)
        sec_lb.selection_clear(0, tk.END)
        
        # Выделяем новое
        hour_lb.selection_set(h)
        hour_lb.see(h)
        min_lb.selection_set(m)
        min_lb.see(m)
        sec_lb.selection_set(s)
        sec_lb.see(s)
        
        # Обновляем переменные и метки
        h_var.set(h)
        m_var.set(m)
        s_var.set(s)
        hour_l.config(text=f"{h:02d}")
        min_l.config(text=f"{m:02d}")
        sec_l.config(text=f"{s:02d}")

    def update_from_var(self, *args):
        """Обновление виджета из переменной"""
        value = self.textvariable.get()
        if value and len(value) == 17:
            current = self.entry.get()
            if current != value:
                self.entry.delete(0, tk.END)
                self.entry.insert(0, value)
    
    def get(self):
        """Получить значение"""
        return self.entry.get()


class MultiFileNetworkVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("DMR Multi-File Network Connections")
        self.root.geometry("1400x900")
        
        # List of files - загружаем все файлы из директории data
        data_directory = load_data_directory()
        self.file_paths = []
        
        # Получаем все .txt файлы из директории data
        if os.path.exists(data_directory):
            for filename in os.listdir(data_directory):
                if filename.endswith('.txt'):
                    file_path = os.path.join(data_directory, filename)
                    self.file_paths.append(file_path)
            
            # Сортируем файлы по имени
            self.file_paths.sort()
            print(f"Найдено {len(self.file_paths)} файлов в директории {data_directory}")
        else:
            print(f"Директория {data_directory} не найдена")
            self.file_paths = []
        
        # Selected files (all by default)
        self.selected_files = set(range(len(self.file_paths)))
        
        # Unique values for filters
        self.unique_events = set()
        self.unique_timeslots = set()
        self.unique_color_codes = set()
        self.unique_algorithms = set()
        self.unique_keys = set()
        self.unique_details = set()
        self.details_count = {}  # {detail: count} for DETAILS
        self.from_identifiers = {}  # {identifier: count} for FROM
        self.to_identifiers = {}    # {identifier: count} for TO
        
        # Variables for new filters
        self.duration_from_var = tk.StringVar(value="")
        self.duration_to_var = tk.StringVar(value="")
        self.selected_event = tk.StringVar(value="All")
        self.selected_timeslot = tk.StringVar(value="All")
        self.selected_color_code = tk.StringVar(value="All")
        self.selected_algorithm = tk.StringVar(value="All")
        self.selected_key = tk.StringVar(value="All")
        self.selected_details = set()  # Set of selected DETAILS
        self.selected_from_ids = set()  # Set of selected FROM identifiers
        self.selected_to_ids = set()    # Set of selected TO identifiers
        
        # PARAMETERS FROM WORKING CODE
        self.column_distance = 400  # Distance between FROM and TO columns
        self.node_width = 66  # Node width (8 characters × 7 pixels + padding)
        self.node_height = 20  # Node height
        self.node_spacing = 3  # Distance between nodes (3 pixels as required)
        self.max_line_width = 8  # Maximum line width for absolute grading
        self.min_line_width = 1  # Minimum line width
        
        # Absolute line width grading based on connection count
        self.line_width_grades = {
            (1, 2): 1.0,
            (3, 5): 1.5,
            (6, 10): 2.0,
            (11, 20): 2.5,
            (21, 50): 3.0,
            (51, 100): 3.5,
            (101, 200): 4.0,
            (201, 300): 5.0,
            (301, 600): 6.0,
            (601, 1000): 7.0,
            (1001, float('inf')): 8.0
        }
        
        # Grid cell sizes (width only, height is dynamic)
        self.cell_width = 600
        self.cell_padding = 20
        self.cell_top_margin = 60
        
        # COLOR SCHEME FROM WORKING CODE
        self.bg_color = "#ffffff"  # White background
        self.line_color = "#404040"  # Dark gray lines
        self.node_border = "#000000"  # Black border
        self.node_bg = "#f0f0f0"  # Light gray node background
        self.text_color = "#000000"  # Black text
        self.count_color = "#606060"  # Gray for counters
        self.selected_bg = "#ffff99"  # Yellow background for selected nodes
        self.highlight_line_color = "#ff0000"  # Red for highlighted connections
        
        # Zoom parameters
        self.zoom_level = 1.0  # As in working code
        self.min_zoom = 0.25
        self.max_zoom = 4.0
        self.zoom_step = 0.25
        
        # Data for all files
        self.file_data = []
        self.filtered_file_data = []  # Filtered data
        
        # Selected nodes for each file
        self.selected_items = {}  # {file_idx: {'from': set(), 'to': set()}}
        self.node_rectangles = {}  # For storing rectangles
        
        # Variables for date filters (will be set after loading data)
        self.date_from_var = tk.StringVar(value="01/01/25 00:00:00")
        self.date_to_var = tk.StringVar(value="31/12/25 23:59:59")
        
        # Variables for canvas dragging
        self.canvas_drag_data = {"x": 0, "y": 0, "dragging": False}
        
        # Initialize PDF exporter
        if REPORTLAB_AVAILABLE:
            self.pdf_exporter = PDFExporter(self)
        else:
            self.pdf_exporter = None
        
        # Initialize vector exporter
        if SVG_AVAILABLE:
            self.vector_exporter = VectorExporter(self)
        else:
            self.vector_exporter = None
        
        # Create interface
        self.setup_ui()
        
        # Load and display data
        self.load_all_data()
        
        # Set date range from loaded data
        self.set_date_range_from_data()
        
        self.draw_all_networks()
    
    def get_line_width_by_count(self, count):
        """Get line width based on absolute connection count"""
        for (min_count, max_count), width in self.line_width_grades.items():
            if min_count <= count <= max_count:
                return width
        return self.min_line_width
    
    
    def export_to_pdf(self):
        """Export current view to PDF file"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Export Error", 
                            "ReportLab library is not installed.\n"
                            "Install it with: pip install reportlab")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save PDF Report"
        )
        
        if filename:
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Exporting...")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - 150
            y = (progress_window.winfo_screenheight() // 2) - 50
            progress_window.geometry(f"+{x}+{y}")
            
            progress_label = tk.Label(progress_window, 
                                    text="Generating PDF report...\nPlease wait...",
                                    font=("Arial", 10))
            progress_label.pack(expand=True)
            
            progress_window.update()
            
            # ИСПРАВЛЕНИЕ: убираем параметр include_visualization
            success = self.pdf_exporter.export_to_pdf(filename)
            
            progress_window.destroy()
            
            if success:
                messagebox.showinfo("Export Complete", 
                                f"PDF report saved successfully to:\n{filename}")
            else:
                messagebox.showerror("Export Error", 
                                "An error occurred while creating the PDF file.")
                


    def export_to_svg(self):
        """Export visualization to SVG vector file"""
        if not SVG_AVAILABLE:
            messagebox.showerror("Export Error", 
                               "svgwrite library is not installed.\n"
                               "Install it with: pip install svgwrite svglib")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG files", "*.svg"), ("All files", "*.*")],
            title="Save as SVG"
        )
        
        if filename:
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Exporting...")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - 150
            y = (progress_window.winfo_screenheight() // 2) - 50
            progress_window.geometry(f"+{x}+{y}")
            
            progress_label = tk.Label(progress_window, 
                                    text="Generating SVG vector file...\nPlease wait...",
                                    font=("Arial", 10))
            progress_label.pack(expand=True)
            
            progress_window.update()
            
            if self.vector_exporter.export_to_svg(filename):
                progress_window.destroy()
                messagebox.showinfo("Export Complete", f"SVG saved to:\n{filename}")
            else:
                progress_window.destroy()
                messagebox.showerror("Export Error", "Failed to export SVG")
    
    def setup_ui(self):
        """Create interface with vector export buttons"""
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top panel with buttons
        top_frame = tk.Frame(main_frame, bg=self.bg_color, height=40)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)
        
        # Button panel
        button_panel = tk.Frame(top_frame, bg=self.bg_color)
        button_panel.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Export to PDF button (with vector graphics)
        if REPORTLAB_AVAILABLE:
            export_pdf_btn = tk.Button(button_panel, text="📄 Export PDF", 
                                     command=self.export_to_pdf,
                                     bg="#FF5722", fg="white",
                                     font=("Arial", 9, "bold"),
                                     relief=tk.RAISED, bd=1)
            export_pdf_btn.pack(side=tk.LEFT, padx=5)
        
        # Export to SVG button (pure vector)
        if SVG_AVAILABLE:
            export_svg_btn = tk.Button(button_panel, text="📐 Export SVG", 
                                     command=self.export_to_svg,
                                     bg="#9C27B0", fg="white",
                                     font=("Arial", 9, "bold"),
                                     relief=tk.RAISED, bd=1)
            export_svg_btn.pack(side=tk.LEFT, padx=5)
        
        # Zoom buttons
        zoom_out_btn = tk.Button(button_panel, text=" - ", command=self.zoom_out,
                                bg="#e0e0e0", width=3, relief=tk.RAISED, bd=1,
                                font=("Arial", 10, "bold"))
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = tk.Label(button_panel, text="100%", bg=self.bg_color,
                                  font=("Arial", 9), width=6)
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        
        zoom_in_btn = tk.Button(button_panel, text=" + ", command=self.zoom_in,
                              bg="#e0e0e0", width=3, relief=tk.RAISED, bd=1,
                              font=("Arial", 10, "bold"))
        zoom_in_btn.pack(side=tk.LEFT, padx=2)
        
        zoom_reset_btn = tk.Button(button_panel, text="Reset", command=self.zoom_reset,
                                 bg="#e0e0e0", relief=tk.RAISED, bd=1, font=("Arial", 9))
        zoom_reset_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = tk.Button(button_panel, text="Refresh", command=self.refresh_all,
                              bg="#e0e0e0", relief=tk.RAISED, bd=1)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Horizontal container
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left filter panel
        filter_frame = tk.Frame(content_frame, bg="#f5f5f5", width=200)
        filter_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
        filter_frame.pack_propagate(False)
        
        # Container for filters
        filter_content = tk.Frame(filter_frame, bg="#f5f5f5")
        filter_content.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # FILE SELECTION BUTTON
        file_select_frame = tk.Frame(filter_content, bg="#f5f5f5")
        file_select_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.select_files_button = tk.Button(file_select_frame, text="SELECT FILES", 
                                           command=self.open_file_selector,
                                           bg="#2196F3", fg="white",
                                           font=("Arial", 10, "bold"),
                                           relief=tk.RAISED, bd=2,
                                           cursor="hand2", width=15)
        self.select_files_button.pack(fill=tk.X)
        
        # IDENTIFIER FILTER BUTTON FROM/TO
        id_filter_frame = tk.Frame(filter_content, bg="#f5f5f5")
        id_filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.id_filter_button = tk.Button(id_filter_frame, text="FROM/TO IDs", 
                                        command=self.open_identifier_selector,
                                        bg="#FF9800", fg="white",
                                        font=("Arial", 10, "bold"),
                                        relief=tk.RAISED, bd=2,
                                        cursor="hand2", width=15)
        self.id_filter_button.pack(fill=tk.X)
        
        # DURATION FILTER
        duration_frame = tk.Frame(filter_content, bg="#f5f5f5")
        duration_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(duration_frame, text="DURATION", bg="#f5f5f5", 
                 fg=self.text_color, font=("Arial", 9, "bold")).pack()
        
        dur_from_frame = tk.Frame(duration_frame, bg="#f5f5f5")
        dur_from_frame.pack(fill=tk.X, pady=2)
        tk.Label(dur_from_frame, text="From:", bg="#f5f5f5", width=7).pack(side=tk.LEFT)
        tk.Entry(dur_from_frame, textvariable=self.duration_from_var, width=10).pack(side=tk.LEFT)
        tk.Label(dur_from_frame, text="sec", bg="#f5f5f5", font=("Arial", 9)).pack(side=tk.LEFT, padx=(2, 0))
        
        dur_to_frame = tk.Frame(duration_frame, bg="#f5f5f5")
        dur_to_frame.pack(fill=tk.X, pady=2)
        tk.Label(dur_to_frame, text="To:", bg="#f5f5f5", width=7).pack(side=tk.LEFT)
        tk.Entry(dur_to_frame, textvariable=self.duration_to_var, width=10).pack(side=tk.LEFT)
        tk.Label(dur_to_frame, text="sec", bg="#f5f5f5", font=("Arial", 9)).pack(side=tk.LEFT, padx=(2, 0))
        
        # EVENT FILTER
        event_frame = tk.Frame(filter_content, bg="#f5f5f5")
        event_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(event_frame, text="EVENT", bg="#f5f5f5", 
                 fg=self.text_color, font=("Arial", 9, "bold")).pack()
        self.event_combo = ttk.Combobox(event_frame, textvariable=self.selected_event, 
                                      state="readonly", width=20)
        self.event_combo.pack()
        
        # TIMESLOT FILTER
        timeslot_frame = tk.Frame(filter_content, bg="#f5f5f5")
        timeslot_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(timeslot_frame, text="TIMESLOT", bg="#f5f5f5", 
                 fg=self.text_color, font=("Arial", 9, "bold")).pack()
        self.timeslot_combo = ttk.Combobox(timeslot_frame, textvariable=self.selected_timeslot, 
                                         state="readonly", width=20)
        self.timeslot_combo.pack()
        
        # COLOR CODE FILTER
        color_frame = tk.Frame(filter_content, bg="#f5f5f5")
        color_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(color_frame, text="COLOR CODE", bg="#f5f5f5", 
                 fg=self.text_color, font=("Arial", 9, "bold")).pack()
        self.color_combo = ttk.Combobox(color_frame, textvariable=self.selected_color_code, 
                                      state="readonly", width=20)
        self.color_combo.pack()
        
        # ALGORITHM FILTER
        algorithm_frame = tk.Frame(filter_content, bg="#f5f5f5")
        algorithm_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(algorithm_frame, text="ALGORITHM", bg="#f5f5f5", 
                 fg=self.text_color, font=("Arial", 9, "bold")).pack()
        self.algorithm_combo = ttk.Combobox(algorithm_frame, textvariable=self.selected_algorithm, 
                                         state="readonly", width=20)
        self.algorithm_combo.pack()
        
        # KEY FILTER
        key_frame = tk.Frame(filter_content, bg="#f5f5f5")
        key_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(key_frame, text="KEY", bg="#f5f5f5", 
                 fg=self.text_color, font=("Arial", 9, "bold")).pack()
        self.key_combo = ttk.Combobox(key_frame, textvariable=self.selected_key, 
                                   state="readonly", width=20)
        self.key_combo.pack()
        
        # DETAILS button
        details_frame = tk.Frame(filter_content, bg="#f5f5f5")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        self.details_button = tk.Button(details_frame, text="DETAILS", 
                                      command=self.open_details_selector,
                                      bg="#9C27B0", fg="white",
                                      font=("Arial", 9, "bold"),
                                      relief=tk.RAISED, bd=2,
                                      cursor="hand2", width=15)
        self.details_button.pack()
        
        # DATE FILTER
        date_filter_frame = tk.Frame(filter_content, bg="#f5f5f5")
        date_filter_frame.pack(fill=tk.X, pady=(0, 20))
        
        # "From" field with mask
        from_frame = tk.Frame(date_filter_frame, bg="#f5f5f5")
        from_frame.pack(fill=tk.X, pady=2)
        
        from_label = tk.Label(from_frame, text="From:", bg="#f5f5f5", 
                             fg=self.text_color, font=("Arial", 9), width=5)
        from_label.pack(side=tk.LEFT)
        
        self.date_from_entry = DateMaskEntry(from_frame, textvariable=self.date_from_var,
                                            bg="#f5f5f5")
        self.date_from_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # "To" field with mask
        to_frame = tk.Frame(date_filter_frame, bg="#f5f5f5")
        to_frame.pack(fill=tk.X, pady=2)
        
        to_label = tk.Label(to_frame, text="To:", bg="#f5f5f5",
                           fg=self.text_color, font=("Arial", 9), width=5)
        to_label.pack(side=tk.LEFT)
        
        self.date_to_entry = DateMaskEntry(to_frame, textvariable=self.date_to_var,
                                          bg="#f5f5f5")
        self.date_to_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # Instructions
        instructions_frame = tk.Frame(filter_content, bg="#f5f5f5")
        instructions_frame.pack(fill=tk.X, pady=10)
        
        # APPLY button at the bottom of filter panel
        apply_frame = tk.Frame(filter_frame, bg="#f5f5f5")
        apply_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.apply_button = tk.Button(apply_frame, text="APPLY", 
                                     command=self.apply_filters,
                                     bg="#4CAF50", fg="white",
                                     font=("Arial", 10, "bold"),
                                     relief=tk.RAISED, bd=2,
                                     cursor="hand2", width=15)
        self.apply_button.pack(fill=tk.X)
        
        # Clear Filter button
        self.clear_button = tk.Button(apply_frame, text="CLEAR FILTER", 
                                     command=self.clear_filters,
                                     bg="#f44336", fg="white",
                                     font=("Arial", 10, "bold"),
                                     relief=tk.RAISED, bd=2,
                                     cursor="hand2", width=15)
        self.clear_button.pack(fill=tk.X, pady=(5, 0))
        
        # Filter status
        self.filter_status = tk.Label(apply_frame, text="No filter applied",
                                     bg="#f5f5f5", fg="#606060",
                                     font=("Arial", 8))
        self.filter_status.pack(pady=(5, 0))
        
        v_separator = tk.Frame(content_frame, width=1, bg="#d0d0d0")
        v_separator.pack(side=tk.LEFT, fill=tk.Y)
        
        # Canvas with scrolling
        canvas_frame = tk.Frame(content_frame, bg=self.bg_color)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.bg_color,
                               yscrollcommand=v_scroll.set,
                               xscrollcommand=h_scroll.set,
                               highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scroll.config(command=self.canvas.yview)
        h_scroll.config(command=self.canvas.xview)
        
        # Bind mouse events for canvas dragging
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Change cursor when dragging
        self.canvas.bind("<Enter>", lambda e: self.canvas.configure(cursor="hand2"))

    def on_canvas_click(self, event):
        """Start dragging the canvas or handle node click"""
        # Check if click is on empty canvas area (not on a node)
        clicked_item = self.canvas.find_closest(event.x, event.y)[0]
        item_tags = self.canvas.gettags(clicked_item)
        
        # If clicked on empty area or lines, start dragging
        if not item_tags or 'current' not in item_tags:
            self.canvas_drag_data["x"] = event.x
            self.canvas_drag_data["y"] = event.y
            self.canvas_drag_data["dragging"] = True
            self.canvas.configure(cursor="fleur")  # Change to move cursor
    
    def on_canvas_drag(self, event):
        """Handle canvas dragging"""
        if self.canvas_drag_data["dragging"]:
            # Calculate the distance moved
            delta_x = event.x - self.canvas_drag_data["x"]
            delta_y = event.y - self.canvas_drag_data["y"]
            
            # Move the canvas view
            self.canvas.xview_scroll(-delta_x, "units")
            self.canvas.yview_scroll(-delta_y, "units")
            
            # Update the drag start position
            self.canvas_drag_data["x"] = event.x
            self.canvas_drag_data["y"] = event.y
    
    def on_canvas_release(self, event):
        """Stop dragging the canvas"""
        if self.canvas_drag_data["dragging"]:
            self.canvas_drag_data["dragging"] = False
            self.canvas.configure(cursor="hand2")  # Change back to hand cursor
    
    def load_more_from_items(self, scrollable_frame, checkbox_vars, sorted_data, start_index, total_items):
        """Load more FROM items dynamically"""
        items_to_load = min(200, total_items - start_index)
        
        for i in range(start_index, start_index + items_to_load):
            identifier, count = sorted_data[i]
            var = tk.BooleanVar(value=(identifier in self.selected_from_ids))
            checkbox_vars.append((identifier, var))
            
            cb_frame = tk.Frame(scrollable_frame, bg="white")
            cb_frame.pack(fill=tk.X, padx=5, pady=1)
            
            cb = tk.Checkbutton(cb_frame, text=str(identifier).rjust(8),
                              variable=var, bg="white",
                              font=("Courier", 9), anchor="w", width=12)
            cb.pack(side=tk.LEFT)
            
            count_label = tk.Label(cb_frame, text=str(count), bg="white",
                                 font=("Arial", 9), fg="#606060", width=6)
            count_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Update button or hide if all loaded
        if start_index + items_to_load >= total_items:
            # Hide load more button
            for widget in scrollable_frame.winfo_children():
                if isinstance(widget, tk.Button) and "Load More" in widget.cget("text"):
                    widget.destroy()
        else:
            # Update button text
            for widget in scrollable_frame.winfo_children():
                if isinstance(widget, tk.Button) and "Load More" in widget.cget("text"):
                    remaining = total_items - (start_index + items_to_load)
                    widget.config(text=f"Load More ({remaining} remaining)")
                    widget.config(command=lambda: self.load_more_from_items(scrollable_frame, checkbox_vars, 
                                                                           sorted_data, start_index + items_to_load, total_items))
                    break

    def load_more_to_items(self, scrollable_frame, checkbox_vars, sorted_data, start_index, total_items):
        """Load more TO items dynamically"""
        items_to_load = min(200, total_items - start_index)
        
        for i in range(start_index, start_index + items_to_load):
            identifier, count = sorted_data[i]
            var = tk.BooleanVar(value=(identifier in self.selected_to_ids))
            checkbox_vars.append((identifier, var))
            
            cb_frame = tk.Frame(scrollable_frame, bg="white")
            cb_frame.pack(fill=tk.X, padx=5, pady=1)
            
            cb = tk.Checkbutton(cb_frame, text=str(identifier).rjust(8),
                              variable=var, bg="white",
                              font=("Courier", 9), anchor="w", width=12)
            cb.pack(side=tk.LEFT)
            
            count_label = tk.Label(cb_frame, text=str(count), bg="white",
                                 font=("Arial", 9), fg="#606060", width=6)
            count_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Update button or hide if all loaded
        if start_index + items_to_load >= total_items:
            # Hide load more button
            for widget in scrollable_frame.winfo_children():
                if isinstance(widget, tk.Button) and "Load More" in widget.cget("text"):
                    widget.destroy()
        else:
            # Update button text
            for widget in scrollable_frame.winfo_children():
                if isinstance(widget, tk.Button) and "Load More" in widget.cget("text"):
                    remaining = total_items - (start_index + items_to_load)
                    widget.config(text=f"Load More ({remaining} remaining)")
                    widget.config(command=lambda: self.load_more_to_items(scrollable_frame, checkbox_vars, 
                                                                         sorted_data, start_index + items_to_load, total_items))
                    break

    def load_all_from_items(self, scrollable_frame, checkbox_vars, sorted_data, start_index, total_items):
        """Load all remaining FROM items at once"""
        remaining_items = total_items - start_index
        
        for i in range(start_index, total_items):
            identifier, count = sorted_data[i]
            var = tk.BooleanVar(value=(identifier in self.selected_from_ids))
            checkbox_vars.append((identifier, var))
            
            cb_frame = tk.Frame(scrollable_frame, bg="white")
            cb_frame.pack(fill=tk.X, padx=5, pady=1)
            
            cb = tk.Checkbutton(cb_frame, text=str(identifier).rjust(8),
                              variable=var, bg="white",
                              font=("Courier", 9), anchor="w", width=12)
            cb.pack(side=tk.LEFT)
            
            count_label = tk.Label(cb_frame, text=str(count), bg="white",
                                 font=("Arial", 9), fg="#606060", width=6)
            count_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Hide load buttons
        for widget in scrollable_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button) and ("Load More" in child.cget("text") or "Load All" in child.cget("text")):
                        widget.destroy()
                        break

    def load_all_to_items(self, scrollable_frame, checkbox_vars, sorted_data, start_index, total_items):
        """Load all remaining TO items at once"""
        remaining_items = total_items - start_index
        
        for i in range(start_index, total_items):
            identifier, count = sorted_data[i]
            var = tk.BooleanVar(value=(identifier in self.selected_to_ids))
            checkbox_vars.append((identifier, var))
            
            cb_frame = tk.Frame(scrollable_frame, bg="white")
            cb_frame.pack(fill=tk.X, padx=5, pady=1)
            
            cb = tk.Checkbutton(cb_frame, text=str(identifier).rjust(8),
                              variable=var, bg="white",
                              font=("Courier", 9), anchor="w", width=12)
            cb.pack(side=tk.LEFT)
            
            count_label = tk.Label(cb_frame, text=str(count), bg="white",
                                 font=("Arial", 9), fg="#606060", width=6)
            count_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Hide load buttons
        for widget in scrollable_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button) and ("Load More" in child.cget("text") or "Load All" in child.cget("text")):
                        widget.destroy()
                        break
    



















    
    def open_identifier_selector(self):
        """Open window for selecting FROM/TO identifiers"""
        selector = tk.Toplevel(self.root)
        selector.title("Select FROM/TO Identifiers")
        selector.geometry("750x700")  # Более компактный размер
        selector.resizable(True, True)  # Разрешить изменение размера
        
        # Show progress window
        progress_window = tk.Toplevel(selector)
        progress_window.title("Loading...")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)
        progress_window.transient(selector)
        progress_window.grab_set()
        
        # Center progress window
        x = (progress_window.winfo_screenwidth() // 2) - 150
        y = (progress_window.winfo_screenheight() // 2) - 50
        progress_window.geometry(f"+{x}+{y}")
        
        # Progress bar with percentage
        progress_frame = tk.Frame(progress_window, bg="#f5f5f5")
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.progress_label = tk.Label(progress_frame, text="Loading identifiers...", 
                                     bg="#f5f5f5", font=("Arial", 10))
        self.progress_label.pack(pady=(0, 5))
        
        # Progress bar with percentage
        self.progress_bar = tk.ttk.Progressbar(progress_frame, mode='determinate', 
                                              maximum=100, length=250)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.percentage_label = tk.Label(progress_frame, text="0%", 
                                       bg="#f5f5f5", font=("Arial", 9))
        self.percentage_label.pack()
        
        # Update the window to show progress
        selector.update()
        progress_window.update()
        
        # Main container
        main_container = tk.Frame(selector, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Container for two columns
        columns_frame = tk.Frame(main_container, bg="#f5f5f5")
        columns_frame.pack(fill=tk.BOTH, expand=True)
        
        # FROM column
        from_column = tk.Frame(columns_frame, bg="#f5f5f5")
        from_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(from_column, text="FROM", bg="#f5f5f5", 
                font=("Arial", 11, "bold")).pack()
        
        from_header = tk.Frame(from_column, bg="#f5f5f5")
        from_header.pack(fill=tk.X)
        tk.Label(from_header, text="ID", bg="#f5f5f5", 
                font=("Arial", 9, "bold"), width=12, anchor="w").pack(side=tk.LEFT, padx=(25, 0))
        tk.Label(from_header, text="Count", bg="#f5f5f5", 
                font=("Arial", 9, "bold"), width=8).pack(side=tk.LEFT)
        
        from_list_frame = tk.Frame(from_column, bg="#f5f5f5")
        from_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # TO column
        to_column = tk.Frame(columns_frame, bg="#f5f5f5")
        to_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(to_column, text="TO", bg="#f5f5f5", 
                font=("Arial", 11, "bold")).pack()
        
        to_header = tk.Frame(to_column, bg="#f5f5f5")
        to_header.pack(fill=tk.X)
        tk.Label(to_header, text="ID", bg="#f5f5f5", 
                font=("Arial", 9, "bold"), width=12, anchor="w").pack(side=tk.LEFT, padx=(25, 0))
        tk.Label(to_header, text="Count", bg="#f5f5f5", 
                font=("Arial", 9, "bold"), width=8).pack(side=tk.LEFT)
        
        to_list_frame = tk.Frame(to_column, bg="#f5f5f5")
        to_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sort identifiers by count (descending order)
        sorted_from_ids = sorted(self.from_identifiers.items(), key=lambda x: x[1], reverse=True)
        sorted_to_ids = sorted(self.to_identifiers.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate total items for progress
        total_from_items = len(sorted_from_ids)
        total_to_items = len(sorted_to_ids)
        total_items = total_from_items + total_to_items
        current_progress = 0
        
        # Initialize if empty
        if not self.selected_from_ids:
            self.selected_from_ids = set(self.from_identifiers.keys())
            print(f"Debug: Initialized FROM IDs with {len(self.selected_from_ids)} items")
        if not self.selected_to_ids:
            self.selected_to_ids = set(self.to_identifiers.keys())
            print(f"Debug: Initialized TO IDs with {len(self.selected_to_ids)} items")
        
        # Checkboxes for FROM
        from_checkboxes = []
        from_checkbox_vars = []
        
        # Update progress for FROM identifiers
        self.progress_label.config(text=f"Loading FROM identifiers ({total_from_items} items)...")
        selector.update()
        progress_window.update()
        
        # Use Treeview for efficient large data handling (решение для больших объемов)
        print(f"Loading ALL {total_from_items} FROM identifiers using Treeview...")
        
        # Create Treeview for FROM identifiers (fast for large datasets)
        from_tree_frame = tk.Frame(from_list_frame, bg="white")
        from_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview with scrollbar and checkboxes
        from_tree = tk.ttk.Treeview(from_tree_frame, columns=("count", "selected"), show="tree headings", height=25)
        from_tree.heading("#0", text="FROM ID", anchor="w")
        from_tree.heading("count", text="Count")
        from_tree.heading("selected", text="✓", anchor="center")
        from_tree.column("#0", width=120, minwidth=100)
        from_tree.column("count", width=60, minwidth=50)
        from_tree.column("selected", width=30, minwidth=30)  # Колонка для галочек
        
        from_tree_scrollbar = tk.Scrollbar(from_tree_frame, orient="vertical", command=from_tree.yview)
        from_tree.configure(yscrollcommand=from_tree_scrollbar.set)
        
        from_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        from_tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store data for search
        self.all_from_data = sorted_from_ids
        self.from_tree = from_tree
        self.from_selected_items = set()
        
        # Load data into Treeview (much faster than individual widgets)
        for i, (identifier, count) in enumerate(sorted_from_ids):
            # Check if item should be selected
            is_selected = identifier in self.selected_from_ids
            if is_selected:
                self.from_selected_items.add(identifier)
            
            # Insert into treeview with checkbox
            checkbox_text = "✓" if is_selected else ""
            item_id = from_tree.insert("", "end", text=str(identifier), values=(count, checkbox_text))
            
            # Update progress every 1000 items (less frequent updates for better performance)
            if i % 1000 == 0:
                current_progress = int(((i + 1) / total_items) * 50)
                self.progress_bar['value'] = current_progress
                self.percentage_label.config(text=f"{current_progress}%")
                self.progress_label.config(text=f"Loading FROM identifiers ({i+1}/{total_from_items})...")
                selector.update()
                progress_window.update()
        
        # Bind click events for checkboxes
        def on_from_click(event):
            item = from_tree.identify_row(event.y)
            column = from_tree.identify_column(event.x)
            
            print(f"Debug: Clicked on item={item}, column={column}")  # Debug info
            
            # Check if clicked on checkbox column (selected) - try different column numbers
            if item and (column == "#3" or column == "#2"):  # Try both possible column numbers
                identifier = from_tree.item(item, "text")
                current_values = from_tree.item(item, "values")
                current_checkbox = current_values[1] if len(current_values) > 1 else ""
                
                print(f"Debug: Toggling {identifier}, current checkbox='{current_checkbox}'")
                
                # Toggle checkbox
                if current_checkbox == "✓":
                    new_checkbox = ""
                    if identifier in self.from_selected_items:
                        self.from_selected_items.discard(identifier)
                else:
                    new_checkbox = "✓"
                    self.from_selected_items.add(identifier)
                
                # Update treeview
                from_tree.item(item, values=(current_values[0], new_checkbox))
                
                # Force treeview to update display
                from_tree.update()
                from_tree.update_idletasks()
                
                print(f"Debug: New checkbox='{new_checkbox}', selected items: {len(self.from_selected_items)}")
                
                # Update selection (but don't apply filters immediately to avoid freezing)
                self.selected_from_ids = self.from_selected_items.copy()
        
        from_tree.bind("<Button-1>", on_from_click)
        
        # Update progress
        current_progress = int((total_from_items / total_items) * 50)  # Approximate progress
        self.progress_bar['value'] = current_progress
        self.percentage_label.config(text=f"{current_progress}%")
        self.progress_label.config(text=f"FROM identifiers loaded ({total_from_items}/{total_from_items})...")
        selector.update()
        progress_window.update()
        
        
        # Search frame for FROM
        from_search_frame = tk.Frame(from_column, bg="#f5f5f5")
        from_search_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Search row with Search and Min count on the same line
        search_row1 = tk.Frame(from_search_frame, bg="#f5f5f5")
        search_row1.pack(fill=tk.X, pady=(0, 2))
        
        tk.Label(search_row1, text="Search:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT)
        from_search_var = tk.StringVar()
        from_search_entry = tk.Entry(search_row1, textvariable=from_search_var, width=12, font=("Arial", 8))
        from_search_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        tk.Label(search_row1, text="Min count:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT)
        from_min_count_var = tk.StringVar()
        from_min_count_entry = tk.Entry(search_row1, textvariable=from_min_count_var, width=8, font=("Arial", 8))
        from_min_count_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        def search_from():
            search_term = from_search_var.get().lower()
            min_count_text = from_min_count_var.get()
            visible_count = 0
            
            try:
                min_count = int(min_count_text) if min_count_text else 0
            except ValueError:
                min_count = 0
            
            # Filter and show items
            for item in from_tree.get_children():
                identifier = from_tree.item(item, "text")
                values = from_tree.item(item, "values")
                count = int(values[0])
                
                # Check if item matches search criteria
                if (count >= min_count and
                    (not search_term or 
                     search_term in identifier.lower() or 
                     search_term in str(count))):
                    from_tree.reattach(item, "", "end")
                    visible_count += 1
                else:
                    from_tree.detach(item)
            
            # Update search status
            if hasattr(self, 'from_search_status'):
                self.from_search_status.destroy()
            self.from_search_status = tk.Label(from_search_frame, 
                                             text=f"Showing {visible_count}/{total_from_items}", 
                                             bg="#f5f5f5", font=("Arial", 8), fg="#666")
            self.from_search_status.pack(side=tk.RIGHT, padx=(5, 0))
        
        from_search_entry.bind("<KeyRelease>", lambda e: search_from())
        from_min_count_entry.bind("<KeyRelease>", lambda e: search_from())
        
        def select_all_from():
            # Select all visible items
            for item in from_tree.get_children():
                identifier = from_tree.item(item, "text")
                current_values = from_tree.item(item, "values")
                from_tree.item(item, values=(current_values[0], "✓"))
                self.from_selected_items.add(identifier)
            
            # Force treeview to update display
            from_tree.update()
            from_tree.update_idletasks()
            
            # Update selection (but don't apply filters immediately to avoid freezing)
            self.selected_from_ids = self.from_selected_items.copy()
        
        def deselect_all_from():
            # Deselect all items
            for item in from_tree.get_children():
                current_values = from_tree.item(item, "values")
                from_tree.item(item, values=(current_values[0], ""))
            
            self.from_selected_items.clear()
            
            # Force treeview to update display
            from_tree.update()
            from_tree.update_idletasks()
            
            # Update selection (but don't apply filters immediately to avoid freezing)
            self.selected_from_ids = self.from_selected_items.copy()
        
        
        # Checkboxes for TO
        to_checkboxes = []
        to_checkbox_vars = []
        
        # Update progress for TO identifiers
        self.progress_label.config(text=f"Loading TO identifiers ({total_to_items} items)...")
        selector.update()
        progress_window.update()
        
        # Use Treeview for TO identifiers (эффективное решение для больших объемов)
        print(f"Loading ALL {total_to_items} TO identifiers using Treeview...")
        
        # Create Treeview for TO identifiers (fast for large datasets)
        to_tree_frame = tk.Frame(to_list_frame, bg="white")
        to_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview with scrollbar and checkboxes
        to_tree = tk.ttk.Treeview(to_tree_frame, columns=("count", "selected"), show="tree headings", height=25)
        to_tree.heading("#0", text="TO ID", anchor="w")
        to_tree.heading("count", text="Count")
        to_tree.heading("selected", text="✓", anchor="center")
        to_tree.column("#0", width=120, minwidth=100)
        to_tree.column("count", width=60, minwidth=50)
        to_tree.column("selected", width=30, minwidth=30)  # Колонка для галочек
        
        to_tree_scrollbar = tk.Scrollbar(to_tree_frame, orient="vertical", command=to_tree.yview)
        to_tree.configure(yscrollcommand=to_tree_scrollbar.set)
        
        to_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        to_tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store data for search
        self.all_to_data = sorted_to_ids
        self.to_tree = to_tree
        self.to_selected_items = set()
        
        # Load data into Treeview (much faster than individual widgets)
        for i, (identifier, count) in enumerate(sorted_to_ids):
            # Check if item should be selected
            is_selected = identifier in self.selected_to_ids
            if is_selected:
                self.to_selected_items.add(identifier)
            
            # Insert into treeview with checkbox
            checkbox_text = "✓" if is_selected else ""
            item_id = to_tree.insert("", "end", text=str(identifier), values=(count, checkbox_text))
            
            # Update progress every 1000 items (less frequent updates for better performance)
            if i % 1000 == 0:
                current_progress = int(((total_from_items + i + 1) / total_items) * 100)
                self.progress_bar['value'] = current_progress
                self.percentage_label.config(text=f"{current_progress}%")
                self.progress_label.config(text=f"Loading TO identifiers ({i+1}/{total_to_items})...")
                selector.update()
                progress_window.update()
        
        # Bind click events for checkboxes
        def on_to_click(event):
            item = to_tree.identify_row(event.y)
            column = to_tree.identify_column(event.x)
            
            print(f"Debug TO: Clicked on item={item}, column={column}")  # Debug info
            
            # Check if clicked on checkbox column (selected) - try different column numbers
            if item and (column == "#3" or column == "#2"):  # Try both possible column numbers
                identifier = to_tree.item(item, "text")
                current_values = to_tree.item(item, "values")
                current_checkbox = current_values[1] if len(current_values) > 1 else ""
                
                print(f"Debug TO: Toggling {identifier}, current checkbox='{current_checkbox}'")
                
                # Toggle checkbox
                if current_checkbox == "✓":
                    new_checkbox = ""
                    if identifier in self.to_selected_items:
                        self.to_selected_items.discard(identifier)
                else:
                    new_checkbox = "✓"
                    self.to_selected_items.add(identifier)
                
                # Update treeview
                to_tree.item(item, values=(current_values[0], new_checkbox))
                
                # Force treeview to update display
                to_tree.update()
                to_tree.update_idletasks()
                
                print(f"Debug TO: New checkbox='{new_checkbox}', selected items: {len(self.to_selected_items)}")
                
                # Update selection (but don't apply filters immediately to avoid freezing)
                self.selected_to_ids = self.to_selected_items.copy()
        
        to_tree.bind("<Button-1>", on_to_click)
        
        # Update progress
        current_progress = int(((total_from_items + total_to_items) / total_items) * 100)
        self.progress_bar['value'] = current_progress
        self.percentage_label.config(text=f"{current_progress}%")
        self.progress_label.config(text=f"TO identifiers loaded ({total_to_items}/{total_to_items})...")
        selector.update()
        progress_window.update()
        
        
        # TO control buttons and search
        to_buttons_frame = tk.Frame(to_column, bg="#f5f5f5")
        to_buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Search frame for TO
        to_search_frame = tk.Frame(to_column, bg="#f5f5f5")
        to_search_frame.pack(fill=tk.X, pady=(2, 0))
        
        # Search row with Search and Min count on the same line
        to_search_row1 = tk.Frame(to_search_frame, bg="#f5f5f5")
        to_search_row1.pack(fill=tk.X, pady=(0, 2))
        
        tk.Label(to_search_row1, text="Search:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT)
        to_search_var = tk.StringVar()
        to_search_entry = tk.Entry(to_search_row1, textvariable=to_search_var, width=12, font=("Arial", 8))
        to_search_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        tk.Label(to_search_row1, text="Min count:", bg="#f5f5f5", font=("Arial", 8)).pack(side=tk.LEFT)
        to_min_count_var = tk.StringVar()
        to_min_count_entry = tk.Entry(to_search_row1, textvariable=to_min_count_var, width=8, font=("Arial", 8))
        to_min_count_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        def search_to():
            search_term = to_search_var.get().lower()
            min_count_text = to_min_count_var.get()
            visible_count = 0
            
            try:
                min_count = int(min_count_text) if min_count_text else 0
            except ValueError:
                min_count = 0
            
            # Filter and show items
            for item in to_tree.get_children():
                identifier = to_tree.item(item, "text")
                values = to_tree.item(item, "values")
                count = int(values[0])
                
                # Check if item matches search criteria
                if (count >= min_count and
                    (not search_term or 
                     search_term in identifier.lower() or 
                     search_term in str(count))):
                    to_tree.reattach(item, "", "end")
                    visible_count += 1
                else:
                    to_tree.detach(item)
            
            # Update search status
            if hasattr(self, 'to_search_status'):
                self.to_search_status.destroy()
            self.to_search_status = tk.Label(to_search_frame, 
                                            text=f"Showing {visible_count}/{total_to_items}", 
                                            bg="#f5f5f5", font=("Arial", 8), fg="#666")
            self.to_search_status.pack(side=tk.RIGHT, padx=(5, 0))
        
        to_search_entry.bind("<KeyRelease>", lambda e: search_to())
        to_min_count_entry.bind("<KeyRelease>", lambda e: search_to())
        
        def select_all_to():
            # Select all visible items
            for item in to_tree.get_children():
                identifier = to_tree.item(item, "text")
                current_values = to_tree.item(item, "values")
                to_tree.item(item, values=(current_values[0], "✓"))
                self.to_selected_items.add(identifier)
            
            # Force treeview to update display
            to_tree.update()
            to_tree.update_idletasks()
            
            # Update selection (but don't apply filters immediately to avoid freezing)
            self.selected_to_ids = self.to_selected_items.copy()
        
        def deselect_all_to():
            # Deselect all items
            for item in to_tree.get_children():
                current_values = to_tree.item(item, "values")
                to_tree.item(item, values=(current_values[0], ""))
            
            self.to_selected_items.clear()
            
            # Force treeview to update display
            to_tree.update()
            to_tree.update_idletasks()
            
            # Update selection (but don't apply filters immediately to avoid freezing)
            self.selected_to_ids = self.to_selected_items.copy()
        
        
        # Complete progress and close window
        self.progress_bar['value'] = 100
        self.percentage_label.config(text="100%")
        self.progress_label.config(text="Loading completed!")
        selector.update()
        progress_window.update()
        
        # Small delay to show completion
        selector.after(500, lambda: progress_window.destroy())
        
        # Add proper window close handling
        def on_closing():
            try:
                selector.destroy()
            except:
                pass
        
        selector.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Control buttons - all in one row
        button_frame = tk.Frame(main_container, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # All buttons in one row
        control_frame = tk.Frame(button_frame, bg="#f5f5f5")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Apply button function
        def apply_identifier_selection():
            # Use the current state from self.from_selected_items and self.to_selected_items
            # instead of reading from Treeview (which may be out of sync)
            self.selected_from_ids = self.from_selected_items.copy()
            self.selected_to_ids = self.to_selected_items.copy()
            
            print(f"Debug: Selected FROM IDs: {len(self.selected_from_ids)} items")
            print(f"Debug: Selected TO IDs: {len(self.selected_to_ids)} items")
            print(f"Debug: FROM IDs: {list(self.selected_from_ids)[:5]}...")  # Показываем первые 5
            print(f"Debug: TO IDs: {list(self.selected_to_ids)[:5]}...")      # Показываем первые 5
            
            selector.destroy()
            
            # Show progress for applying filters
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Applying Filters...")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Center progress window
            x = (progress_window.winfo_screenwidth() // 2) - 150
            y = (progress_window.winfo_screenheight() // 2) - 50
            progress_window.geometry(f"+{x}+{y}")
            
            progress_label = tk.Label(progress_window, 
                                    text="Applying filters...\nPlease wait...",
                                    font=("Arial", 10))
            progress_label.pack(expand=True)
            
            progress_window.update()
            
            # Apply filters asynchronously
            self.apply_filters_async(progress_window)
        
        # FROM buttons on the left
        from_buttons_frame = tk.Frame(control_frame, bg="#f5f5f5")
        from_buttons_frame.pack(side=tk.LEFT)
        
        tk.Button(from_buttons_frame, text="Select All FROM", command=select_all_from,
                 bg="#4CAF50", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(from_buttons_frame, text="Deselect All FROM", command=deselect_all_from,
                 bg="#f44336", fg="white", font=("Arial", 8)).pack(side=tk.LEFT)
        
        # TO buttons on the right
        to_buttons_frame = tk.Frame(control_frame, bg="#f5f5f5")
        to_buttons_frame.pack(side=tk.RIGHT)
        
        tk.Button(to_buttons_frame, text="Select All TO", command=select_all_to,
                 bg="#4CAF50", fg="white", font=("Arial", 8)).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(to_buttons_frame, text="Deselect All TO", command=deselect_all_to,
                 bg="#f44336", fg="white", font=("Arial", 8)).pack(side=tk.LEFT)
        
        # APPLY button in the center
        apply_btn = tk.Button(control_frame, text="APPLY",
                           command=apply_identifier_selection,
                 bg="#2196F3", fg="white",
                           font=("Arial", 10, "bold"),
                 width=10, height=1)
        apply_btn.pack(expand=True)
        
        # Make window modal
        selector.transient(self.root)
        selector.grab_set()
        
        # Center window
        selector.update_idletasks()
        x = (selector.winfo_screenwidth() // 2) - 300
        y = (selector.winfo_screenheight() // 2) - 225
        selector.geometry(f"+{x}+{y}")
    



















    
    def open_details_selector(self):
        """Открыть окно выбора DETAILS"""
        selector = tk.Toplevel(self.root)
        selector.title("Select Details")
        selector.geometry("420x700")  # Увеличено в два раза по высоте
        selector.resizable(True, True)  # Разрешить изменение размера
        
        # Основной контейнер
        main_container = tk.Frame(selector, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Список с чекбоксами
        details_frame = tk.Frame(main_container, bg="#f5f5f5")
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Контейнер для скроллинга (увеличена высота)
        canvas = tk.Canvas(details_frame, bg="white", height=500)
        scrollbar = tk.Scrollbar(details_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        # Упаковываем canvas и scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Добавляем поддержку колесика мыши для скролла
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        
        # Создаем чекбоксы для каждого уникального DETAILS
        checkboxes = []
        checkbox_vars = []
        
        sorted_details = sorted(self.unique_details)
        for detail in sorted_details:
            # По умолчанию все DETAILS выбраны, если selected_details пустой
            is_selected = detail in self.selected_details if self.selected_details else True
            var = tk.BooleanVar(value=is_selected)
            checkbox_vars.append((detail, var))
            
            cb_frame = tk.Frame(scrollable_frame, bg="white")
            cb_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Добавляем количество в скобках
            count = self.details_count.get(detail, 0)
            display_text = f"{detail} ({count})"
            cb = tk.Checkbutton(cb_frame, text=display_text,
                              variable=var, bg="white",
                              font=("Arial", 9), anchor="w")
            cb.pack(fill=tk.X)
            checkboxes.append(cb)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Кнопки управления
        button_frame = tk.Frame(main_container, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Кнопки Убрать все / Выделить все
        control_frame = tk.Frame(button_frame, bg="#f5f5f5")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        def deselect_all():
            for _, var in checkbox_vars:
                var.set(False)
        
        def select_all():
            for _, var in checkbox_vars:
                var.set(True)
        
        deselect_btn = tk.Button(control_frame, text="Deselect All",
                              command=deselect_all,
                              bg="#e0e0e0", font=("Arial", 9),
                              width=12)
        deselect_btn.pack(side=tk.LEFT, padx=5)
        
        select_all_btn = tk.Button(control_frame, text="Select All",
                                 command=select_all,
                                 bg="#e0e0e0", font=("Arial", 9),
                                 width=12)
        select_all_btn.pack(side=tk.RIGHT, padx=5)
        
        # Кнопка применить
        def apply_details_selection():
            self.selected_details.clear()
            for detail, var in checkbox_vars:
                if var.get():
                    self.selected_details.add(detail)
            print(f"Selected DETAILS: {self.selected_details}")
            selector.destroy()
            # Автоматически применяем фильтры после выбора
            self.apply_filters()
        
        apply_btn = tk.Button(button_frame, text="APPLY",
                           command=apply_details_selection,
                           bg="#4CAF50", fg="white",
                           font=("Arial", 10, "bold"),
                           width=20, height=2)
        apply_btn.pack()
        
        # Делаем окно модальным
        selector.transient(self.root)
        selector.grab_set()
        
        # Центрируем окно
        selector.update_idletasks()
        x = (selector.winfo_screenwidth() // 2) - 200
        y = (selector.winfo_screenheight() // 2) - 175
        selector.geometry(f"+{x}+{y}")
    
    def open_file_selector(self):
        """Открыть окно выбора файлов"""
        selector = tk.Toplevel(self.root)
        selector.title("Select Files")
        selector.geometry("450x700")
        selector.resizable(False, False)
        
        # Основной контейнер
        main_container = tk.Frame(selector, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Список файлов с чекбоксами
        files_frame = tk.Frame(main_container, bg="#f5f5f5")
        files_frame.pack(fill=tk.BOTH, expand=True)
        
        # Контейнер для скроллинга
        canvas = tk.Canvas(files_frame, bg="white", height=500)
        scrollbar = tk.Scrollbar(files_frame, orient="vertical", command=canvas.yview, width=20)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Создаем чекбоксы для каждого файла
        checkboxes = []
        checkbox_vars = []
        
        for idx, file_path in enumerate(self.file_paths):
            var = tk.BooleanVar(value=(idx in self.selected_files))
            checkbox_vars.append(var)
            
            cb_frame = tk.Frame(scrollable_frame, bg="white")
            cb_frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Получаем количество записей для этого файла
            session_count = 0
            if idx < len(self.file_data) and self.file_data[idx]:
                connections = self.file_data[idx].get('connections', {})
                session_count = sum(connections.values())
            
            # Создаем текст с количеством записей
            filename = os.path.basename(file_path)
            display_text = f"{filename} ({session_count} sessions)"
            
            cb = tk.Checkbutton(cb_frame, text=display_text,
                              variable=var, bg="white",
                              font=("Arial", 9), anchor="w")
            cb.pack(fill=tk.X)
            checkboxes.append(cb)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Добавляем поддержку колесика мыши
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', bind_to_mousewheel)
        canvas.bind('<Leave>', unbind_from_mousewheel)
        
        # Кнопки управления
        button_frame = tk.Frame(main_container, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Кнопки Убрать все / Выделить все
        control_frame = tk.Frame(button_frame, bg="#f5f5f5")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        def deselect_all():
            for var in checkbox_vars:
                var.set(False)
        
        def select_all():
            for var in checkbox_vars:
                var.set(True)
        
        deselect_btn = tk.Button(control_frame, text="Deselect All",
                              command=deselect_all,
                              bg="#e0e0e0", font=("Arial", 9),
                              width=12)
        deselect_btn.pack(side=tk.LEFT, padx=5)
        
        select_all_btn = tk.Button(control_frame, text="Select All",
                                 command=select_all,
                                 bg="#e0e0e0", font=("Arial", 9),
                                 width=12)
        select_all_btn.pack(side=tk.RIGHT, padx=5)
        
        # Кнопка применить
        def apply_file_selection():
            self.selected_files.clear()
            for idx, var in enumerate(checkbox_vars):
                if var.get():
                    self.selected_files.add(idx)
            
            selector.destroy()
            self.draw_all_networks()
        
        apply_btn = tk.Button(button_frame, text="APPLY",
                           command=apply_file_selection,
                           bg="#4CAF50", fg="white",
                           font=("Arial", 10, "bold"),
                           width=20, height=1)
        apply_btn.pack()
        
        # Делаем окно модальным
        selector.transient(self.root)
        selector.grab_set()
        
        # Центрируем окно
        selector.update_idletasks()
        x = (selector.winfo_screenwidth() // 2) - 200
        y = (selector.winfo_screenheight() // 2) - 175
        selector.geometry(f"+{x}+{y}")
    
    def update_comboboxes(self):
        """Обновление комбобоксов с уникальными значениями"""
        # EVENT
        event_values = ['All'] + sorted(self.unique_events)
        self.event_combo['values'] = event_values
        if self.selected_event.get() not in event_values:
            self.selected_event.set('All')
        
        # TIMESLOT
        timeslot_values = ['All'] + sorted(self.unique_timeslots)
        self.timeslot_combo['values'] = timeslot_values
        if self.selected_timeslot.get() not in timeslot_values:
            self.selected_timeslot.set('All')
        
        # COLOR CODE
        color_values = ['All'] + sorted(self.unique_color_codes)
        self.color_combo['values'] = color_values
        if self.selected_color_code.get() not in color_values:
            self.selected_color_code.set('All')
        
        # ALGORITHM
        algorithm_values = ['All'] + sorted(self.unique_algorithms)
        self.algorithm_combo['values'] = algorithm_values
        if self.selected_algorithm.get() not in algorithm_values:
            self.selected_algorithm.set('All')
        
        # KEY
        key_values = ['All'] + sorted(self.unique_keys)
        self.key_combo['values'] = key_values
        if self.selected_key.get() not in key_values:
            self.selected_key.set('All')
    
    def parse_date(self, date_str):
        """Парсинг даты из формата DD/MM/YY HH:MM:SS"""
        try:
            return datetime.strptime(date_str, "%d/%m/%y %H:%M:%S")
        except:
            return None
        
    def parse_timestamp(self, timestamp_str):
        """Парсинг даты из формата YYYY:MM:DD:HH:MM:SS (формат из CSV)"""
        try:
            return datetime.strptime(timestamp_str, "%Y:%m:%d:%H:%M:%S")
        except:
            return None
    
    def apply_filters_async(self, progress_window):
        """Apply filters asynchronously with progress updates"""
        def apply_filters_worker():
            try:
                # Get filter values
                date_from_str = self.date_from_var.get()
                date_to_str = self.date_to_var.get()
                
                date_from = self.parse_date(date_from_str)
                date_to = self.parse_date(date_to_str)
                
                if not date_from or not date_to:
                    progress_window.after(0, lambda: progress_window.destroy())
                    self.filter_status.config(text="Invalid date format", fg="red")
                    return
                
                # Get filter values
                duration_from = self.duration_from_var.get()
                duration_to = self.duration_to_var.get()
                event_filter = self.selected_event.get()
                timeslot_filter = self.selected_timeslot.get()
                color_code_filter = self.selected_color_code.get()
                algorithm_filter = self.selected_algorithm.get()
                key_filter = self.selected_key.get()
                
                # Convert duration from seconds to milliseconds
                try:
                    dur_from_ms = float(duration_from) * 1000 if duration_from else None
                    dur_to_ms = float(duration_to) * 1000 if duration_to else None
                except:
                    dur_from_ms = dur_to_ms = None
                
                # Filter data
                self.filtered_file_data = []
                total_connections = 0
                total_with_dates = 0
                total_filtered = 0
                
                # Update progress
                progress_window.after(0, lambda: progress_window.destroy())
                
                for data in self.file_data:
                    filtered_connections = defaultdict(int)
                    filtered_from_counts = defaultdict(int)
                    filtered_to_counts = defaultdict(int)
                    filtered_dates = defaultdict(list)
                    filtered_details = defaultdict(list)
                    
                    # Get connection details if they exist
                    connection_details = data.get('connection_details', {})
                    
                    for (from_id, to_id), details_list in connection_details.items():
                        for detail in details_list:
                            total_connections += 1
                            
                            # Check all filters
                            passes_filter = True
                            
                            # Filter by FROM/TO identifiers
                            if self.selected_from_ids and from_id not in self.selected_from_ids:
                                passes_filter = False
                            if self.selected_to_ids and to_id not in self.selected_to_ids:
                                passes_filter = False
                            
                            # Filter by date
                            if detail['timestamp']:
                                total_with_dates += 1
                                if not (date_from <= detail['timestamp'] <= date_to):
                                    passes_filter = False
                            else:
                                passes_filter = False  # Skip entries without date
                            
                            # Filter by duration (compare in milliseconds)
                            if dur_from_ms is not None or dur_to_ms is not None:
                                try:
                                    duration_ms = float(detail['duration_ms']) if detail['duration_ms'] else 0
                                    if dur_from_ms is not None and duration_ms < dur_from_ms:
                                        passes_filter = False
                                    if dur_to_ms is not None and duration_ms > dur_to_ms:
                                        passes_filter = False
                                except:
                                    passes_filter = False
                            
                            # Filter by EVENT
                            if event_filter != 'All' and detail['event'] != event_filter:
                                passes_filter = False
                            
                            # Filter by TIMESLOT
                            if timeslot_filter != 'All' and detail['timeslot'] != timeslot_filter:
                                passes_filter = False
                            
                            # Filter by COLOR_CODE
                            if color_code_filter != 'All' and detail['color_code'] != color_code_filter:
                                passes_filter = False
                            
                            # Filter by ALGORITHM
                            if algorithm_filter != 'All' and detail['algorithm'] != algorithm_filter:
                                passes_filter = False
                            
                            # Filter by KEY
                            if key_filter != 'All' and detail['key'] != key_filter:
                                passes_filter = False
                            
                            # Filter by DETAILS
                            if self.selected_details and detail.get('details', '') not in self.selected_details:
                                passes_filter = False
                            
                            if passes_filter:
                                filtered_connections[(from_id, to_id)] += 1
                                filtered_from_counts[from_id] += 1
                                filtered_to_counts[to_id] += 1
                                if detail['timestamp']:
                                    filtered_dates[(from_id, to_id)].append(detail['timestamp'])
                                filtered_details[(from_id, to_id)].append(detail)
                                total_filtered += 1
                    
                    filtered_data = {
                        'file_path': data['file_path'],
                        'filename': data['filename'],
                        'frequency': data['frequency'],
                        'connections': dict(filtered_connections),
                        'from_counts': dict(filtered_from_counts),
                        'to_counts': dict(filtered_to_counts),
                        'connection_dates': dict(filtered_dates),
                        'connection_details': dict(filtered_details)
                    }
                    self.filtered_file_data.append(filtered_data)
                
                # Update status with detailed information
                if total_with_dates > 0:
                    percent = int((total_filtered / total_with_dates) * 100) if total_with_dates > 0 else 0
                    self.filter_status.config(
                        text=f"Filtered: {total_filtered}/{total_with_dates} ({percent}%)",
                        fg="green" if total_filtered > 0 else "orange"
                    )
                else:
                    self.filter_status.config(
                        text="No date data found",
                        fg="red"
                    )
                
                print(f"Debug: Total connections: {total_connections}")
                print(f"Debug: With dates: {total_with_dates}")
                print(f"Debug: Filtered: {total_filtered}")
                print(f"Debug: Date range: {date_from} to {date_to}")
                print(f"Debug: Selected DETAILS: {self.selected_details}")
                print(f"Debug: FROM filter: {len(self.selected_from_ids)} selected FROM IDs")
                print(f"Debug: TO filter: {len(self.selected_to_ids)} selected TO IDs")
                
                # Force UI update
                self.root.after(0, lambda: self.root.update())
                
                # Redraw with filtered data (also async with progress)
                self.root.after(0, lambda: self.draw_all_networks_async(use_filtered=True))
                
                # Force final UI update
                self.root.after(0, lambda: self.root.update())
                
            except Exception as e:
                print(f"Error applying filters: {e}")
                progress_window.after(0, lambda: progress_window.destroy())
                self.filter_status.config(text="Error applying filters", fg="red")
        
        # Start the worker in a separate thread
        import threading
        thread = threading.Thread(target=apply_filters_worker)
        thread.daemon = True
        thread.start()
    
    def apply_filters(self):
        """Apply filters to data"""
        date_from_str = self.date_from_var.get()
        date_to_str = self.date_to_var.get()
        
        date_from = self.parse_date(date_from_str)
        date_to = self.parse_date(date_to_str)
        
        if not date_from or not date_to:
            self.filter_status.config(text="Invalid date format", fg="red")
            return
        
        # Get filter values
        duration_from = self.duration_from_var.get()
        duration_to = self.duration_to_var.get()
        event_filter = self.selected_event.get()
        timeslot_filter = self.selected_timeslot.get()
        color_code_filter = self.selected_color_code.get()
        algorithm_filter = self.selected_algorithm.get()
        key_filter = self.selected_key.get()
        
        # Convert duration from seconds to milliseconds
        try:
            dur_from_ms = float(duration_from) * 1000 if duration_from else None
            dur_to_ms = float(duration_to) * 1000 if duration_to else None
        except:
            dur_from_ms = dur_to_ms = None
        
        # Filter data
        self.filtered_file_data = []
        total_connections = 0
        total_with_dates = 0
        total_filtered = 0
        
        for data in self.file_data:
            filtered_connections = defaultdict(int)
            filtered_from_counts = defaultdict(int)
            filtered_to_counts = defaultdict(int)
            filtered_dates = defaultdict(list)
            filtered_details = defaultdict(list)
            
            # Get connection details if they exist
            connection_details = data.get('connection_details', {})
            
            for (from_id, to_id), details_list in connection_details.items():
                for detail in details_list:
                    total_connections += 1
                    
                    # Check all filters
                    passes_filter = True
                    
                    # Filter by FROM/TO identifiers
                    if self.selected_from_ids and from_id not in self.selected_from_ids:
                        passes_filter = False
                    if self.selected_to_ids and to_id not in self.selected_to_ids:
                        passes_filter = False
                    
                    # Filter by date
                    if detail['timestamp']:
                        total_with_dates += 1
                        if not (date_from <= detail['timestamp'] <= date_to):
                            passes_filter = False
                    else:
                        passes_filter = False  # Skip entries without date
                    
                    # Filter by duration (compare in milliseconds)
                    if dur_from_ms is not None or dur_to_ms is not None:
                        try:
                            duration_ms = float(detail['duration_ms']) if detail['duration_ms'] else 0
                            if dur_from_ms is not None and duration_ms < dur_from_ms:
                                passes_filter = False
                            if dur_to_ms is not None and duration_ms > dur_to_ms:
                                passes_filter = False
                        except:
                            passes_filter = False
                    
                    # Filter by EVENT
                    if event_filter != 'All' and detail['event'] != event_filter:
                        passes_filter = False
                    
                    # Filter by TIMESLOT
                    if timeslot_filter != 'All' and detail['timeslot'] != timeslot_filter:
                        passes_filter = False
                    
                    # Filter by COLOR_CODE
                    if color_code_filter != 'All' and detail['color_code'] != color_code_filter:
                        passes_filter = False
                    
                    # Filter by ALGORITHM
                    if algorithm_filter != 'All' and detail['algorithm'] != algorithm_filter:
                        passes_filter = False
                    
                    # Filter by KEY
                    if key_filter != 'All' and detail['key'] != key_filter:
                        passes_filter = False
                    
                    # Filter by DETAILS
                    if self.selected_details and detail.get('details', '') not in self.selected_details:
                        passes_filter = False
                        print(f"DETAILS filter: {detail.get('details', '')} not in {self.selected_details}")
                    
                    if passes_filter:
                        filtered_connections[(from_id, to_id)] += 1
                        filtered_from_counts[from_id] += 1
                        filtered_to_counts[to_id] += 1
                        if detail['timestamp']:
                            filtered_dates[(from_id, to_id)].append(detail['timestamp'])
                        filtered_details[(from_id, to_id)].append(detail)
                        total_filtered += 1
            
            filtered_data = {
                'file_path': data['file_path'],
                'filename': data['filename'],
                'frequency': data['frequency'],
                'connections': dict(filtered_connections),
                'from_counts': dict(filtered_from_counts),
                'to_counts': dict(filtered_to_counts),
                'connection_dates': dict(filtered_dates),
                'connection_details': dict(filtered_details)
            }
            self.filtered_file_data.append(filtered_data)
        
        # Update status with detailed information
        if total_with_dates > 0:
            percent = int((total_filtered / total_with_dates) * 100) if total_with_dates > 0 else 0
            self.filter_status.config(
                text=f"Filtered: {total_filtered}/{total_with_dates} ({percent}%)",
                fg="green" if total_filtered > 0 else "orange"
            )
        else:
            self.filter_status.config(
                text="No date data found",
                fg="red"
            )
        
        print(f"Debug: Total connections: {total_connections}")
        print(f"Debug: With dates: {total_with_dates}")
        print(f"Debug: Filtered: {total_filtered}")
        print(f"Debug: Date range: {date_from} to {date_to}")
        print(f"Debug: Selected DETAILS: {self.selected_details}")
        print(f"Debug: FROM filter: {len(self.selected_from_ids)} selected FROM IDs")
        print(f"Debug: TO filter: {len(self.selected_to_ids)} selected TO IDs")
        
        # Force UI update
        self.root.update()
        
        # Redraw with filtered data
        self.draw_all_networks(use_filtered=True)
        
        # Force final UI update
        self.root.update()
    
    def clear_filters(self):
        """Сброс всех фильтров"""
        # Копируем все данные без фильтрации
        self.filtered_file_data = []
        
        # Сбрасываем значения фильтров
        self.duration_from_var.set("")
        self.duration_to_var.set("")
        self.selected_event.set("All")
        self.selected_timeslot.set("All")
        self.selected_color_code.set("All")
        self.selected_algorithm.set("All")
        self.selected_key.set("All")
        self.selected_details.clear()
        # Восстанавливаем все идентификаторы
        self.selected_from_ids = set(self.from_identifiers.keys())
        self.selected_to_ids = set(self.to_identifiers.keys())
        print(f"Debug: Cleared filters - restored {len(self.selected_from_ids)} FROM IDs and {len(self.selected_to_ids)} TO IDs")
        
        # Обновляем статус
        self.filter_status.config(text="No filter applied", fg="#606060")
        
        # Перерисовываем без фильтров
        self.draw_all_networks(use_filtered=False)
    
    def calculate_grid_dimensions(self, num_files):
        """Вычисление размеров сетки"""
        if num_files <= 0:
            return 0, 0
        cols = math.ceil(math.sqrt(num_files))
        rows = math.ceil(num_files / cols)
        return rows, cols
    
    def load_all_data(self):
        """Загрузка данных из всех файлов"""
        self.file_data.clear()
        self.filtered_file_data.clear()
        self.selected_items.clear()
        
        # Очищаем уникальные значения
        self.unique_events.clear()
        self.unique_timeslots.clear()
        self.unique_color_codes.clear()
        self.unique_algorithms.clear()
        self.unique_keys.clear()
        self.unique_details.clear()
        self.details_count.clear()  # Очищаем счетчик DETAILS
        self.from_identifiers.clear()  # Очищаем счетчик FROM идентификаторов
        self.to_identifiers.clear()    # Очищаем счетчик TO идентификаторов
        
        for idx, file_path in enumerate(self.file_paths):
            data = self.load_file_data(file_path)
            if data:
                self.file_data.append(data)
                self.selected_items[idx] = {'from': set(), 'to': set()}
                
                # Собираем уникальные значения
                self.unique_events.update(data.get('events', set()))
                self.unique_timeslots.update(data.get('timeslots', set()))
                self.unique_color_codes.update(data.get('color_codes', set()))
                self.unique_algorithms.update(data.get('algorithms', set()))
                self.unique_keys.update(data.get('keys', set()))
                self.unique_details.update(data.get('details', set()))
                
                # Подсчитываем идентификаторы FROM
                for from_id, count in data['from_counts'].items():
                    if from_id not in self.from_identifiers:
                        self.from_identifiers[from_id] = 0
                    self.from_identifiers[from_id] += count
                
                # Подсчитываем идентификаторы TO
                for to_id, count in data['to_counts'].items():
                    if to_id not in self.to_identifiers:
                        self.to_identifiers[to_id] = 0
                    self.to_identifiers[to_id] += count
        
        # Инициализируем selected_from_ids и selected_to_ids всеми идентификаторами по умолчанию
        if not self.selected_from_ids:
            self.selected_from_ids = set(self.from_identifiers.keys())
        if not self.selected_to_ids:
            self.selected_to_ids = set(self.to_identifiers.keys())
        
        # Обновляем комбобоксы
        self.update_comboboxes()
        
        # Выводим информацию о загруженных файлах
        print(f"Загружено {len(self.file_data)} файлов из {len(self.file_paths)} найденных")
        print(f"Уникальных событий: {len(self.unique_events)}")
        print(f"Уникальных DETAILS: {len(self.unique_details)}")
        print(f"FROM идентификаторов: {len(self.from_identifiers)}")
        print(f"TO идентификаторов: {len(self.to_identifiers)}")
    
    def load_file_data(self, file_path):
        """Загрузка данных из одного файла"""
        connections = defaultdict(int)
        from_counts = defaultdict(int)
        to_counts = defaultdict(int)
        connection_dates = defaultdict(list)  # Список дат для каждого соединения
        
        # Новые структуры для хранения данных по соединениям
        connection_details = defaultdict(list)  # Детальная информация о каждом соединении
        
        # Уникальные значения для фильтров
        events = set()
        timeslots = set()
        color_codes = set()
        algorithms = set()
        keys = set()
        details = set()
        
        # Извлекаем частоту
        frequency = "Unknown"
        try:
            filename = os.path.basename(file_path)
            if '-' in filename:
                parts = filename.replace('.txt', '').split('-')
                if len(parts) == 3:
                    freq_mhz = parts[0]
                    freq_khz = parts[1] + parts[2]
                    frequency = f"{freq_mhz}.{freq_khz} MHz"
        except:
            pass
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = [line for line in file if not line.startswith('#')]
            
            csv_reader = csv.DictReader(lines)
            
            for row in csv_reader:
                from_id = row.get('FROM', '').strip()
                to_id = row.get('TO', '').strip()
                
                # Читаем все поля
                timestamp_str = row.get('TIMESTAMP', '').strip()
                duration_ms = row.get('DURATION_MS', '').strip()
                event = row.get('EVENT', '').strip()
                timeslot = row.get('TIMESLOT', '').strip()
                color_code = row.get('COLOR_CODE', '').strip()
                algorithm = row.get('ALGORITHM', '').strip()
                key = row.get('KEY', '').strip()
                detail = row.get('DETAILS', '').strip()
                
                # Собираем уникальные значения
                if event:
                    events.add(event)
                if timeslot:
                    timeslots.add(timeslot)
                if color_code:
                    color_codes.add(color_code)
                if algorithm:
                    algorithms.add(algorithm)
                if key:
                    keys.add(key)
                if detail:
                    details.add(detail)
                    # Подсчитываем количество DETAILS
                    if detail not in self.details_count:
                        self.details_count[detail] = 0
                    self.details_count[detail] += 1
                
                # Парсим TIMESTAMP
                connection_date = None
                if timestamp_str:
                    timestamp_str = timestamp_str.strip('"')
                    connection_date = self.parse_timestamp(timestamp_str)
                
                if from_id and to_id:
                    connections[(from_id, to_id)] += 1
                    from_counts[from_id] += 1
                    to_counts[to_id] += 1
                    
                    # Сохраняем дату если есть
                    if connection_date:
                        connection_dates[(from_id, to_id)].append(connection_date)
                    
                    # Сохраняем детальную информацию о соединении
                    connection_details[(from_id, to_id)].append({
                        'timestamp': connection_date,
                        'duration_ms': duration_ms,
                        'event': event,
                        'timeslot': timeslot,
                        'color_code': color_code,
                        'algorithm': algorithm,
                        'key': key,
                        'details': detail
                    })
                    
            return {
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'frequency': frequency,
                'connections': connections,
                'from_counts': from_counts,
                'to_counts': to_counts,
                'connection_dates': dict(connection_dates),
                'connection_details': dict(connection_details),
                'events': events,
                'timeslots': timeslots,
                'color_codes': color_codes,
                'algorithms': algorithms,
                'keys': keys,
                'details': details
            }
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    def draw_all_networks_async(self, use_filtered=None):
        """Draw all networks asynchronously with progress"""
        def draw_worker():
            try:
                # Show progress window
                progress_window = tk.Toplevel(self.root)
                progress_window.title("Drawing Networks...")
                progress_window.geometry("300x120")
                progress_window.resizable(False, False)
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                # Center progress window
                x = (progress_window.winfo_screenwidth() // 2) - 150
                y = (progress_window.winfo_screenheight() // 2) - 60
                progress_window.geometry(f"+{x}+{y}")
                
                progress_label = tk.Label(progress_window, 
                                        text="Drawing networks...\nPlease wait...",
                                        font=("Arial", 10))
                progress_label.pack(pady=(10, 5))
                
                # Progress bar
                progress_bar = tk.ttk.Progressbar(progress_window, mode='indeterminate', length=250)
                progress_bar.pack(pady=(0, 10))
                progress_bar.start(10)  # Start the indeterminate progress bar
                
                progress_window.update()
                
                # Call the actual drawing method
                self.draw_all_networks(use_filtered)
                
                # Stop progress bar
                progress_bar.stop()
                
                # Close progress window
                progress_window.after(0, lambda: progress_window.destroy())
                
            except Exception as e:
                print(f"Error drawing networks: {e}")
                if 'progress_window' in locals():
                    progress_window.after(0, lambda: progress_window.destroy())
        
        # Start the worker in a separate thread
        import threading
        thread = threading.Thread(target=draw_worker)
        thread.daemon = True
        thread.start()
    
    def draw_all_networks(self, use_filtered=None):
        """Draw all networks on one canvas"""
        self.canvas.delete("all")
        self.node_rectangles.clear()
        
        # If use_filtered not specified, determine automatically
        if use_filtered is None:
            use_filtered = len(self.filtered_file_data) > 0
        
        # Choose data to display
        data_to_draw = self.filtered_file_data if use_filtered and self.filtered_file_data else self.file_data
        
        # Filter by selected files
        data_to_draw = [data for idx, data in enumerate(data_to_draw) if idx in self.selected_files]
        
        # Filter out files with no data (No data in date range)
        original_count = len(data_to_draw)
        data_to_draw = [data for data in data_to_draw if data.get('connections') and len(data.get('connections', {})) > 0]
        hidden_count = original_count - len(data_to_draw)
        
        if hidden_count > 0:
            print(f"Скрыто {hidden_count} файлов без данных в выбранном диапазоне")
        
        num_files = len(data_to_draw)
        if num_files == 0:
            self.canvas.create_text(400, 200, text="No files with data in selected range", 
                                   font=("Arial", 14), fill=self.text_color)
            return
        
        rows, cols = self.calculate_grid_dimensions(num_files)
        
        # Apply scale
        scaled_cell_width = self.cell_width * self.zoom_level
        scaled_padding = self.cell_padding * self.zoom_level
        scaled_node_height = self.node_height * self.zoom_level
        scaled_node_spacing = self.node_spacing * self.zoom_level
        scaled_top_margin = self.cell_top_margin * self.zoom_level
        
        # Calculate height of each row
        row_heights = []
        for row_idx in range(rows):
            max_height = 0
            for col_idx in range(cols):
                file_idx = row_idx * cols + col_idx
                if file_idx < num_files:
                    data = data_to_draw[file_idx]
                    num_from = len(data['from_counts'])
                    num_to = len(data['to_counts'])
                    max_nodes = max(num_from, num_to)
                    
                    cell_height = (scaled_top_margin + 
                                 max_nodes * (scaled_node_height + scaled_node_spacing) + 
                                 scaled_padding)
                    
                    max_height = max(max_height, cell_height)
            
            row_heights.append(max_height)
        
        # Draw each file with periodic UI updates
        current_y = scaled_padding
        files_drawn = 0
        
        for row_idx in range(rows):
            current_x = scaled_padding
            row_height = row_heights[row_idx]
            
            for col_idx in range(cols):
                display_idx = row_idx * cols + col_idx
                if display_idx < num_files:
                    data = data_to_draw[display_idx]
                    
                    # Find original file index
                    original_idx = -1
                    for orig_idx in self.selected_files:
                        if (use_filtered and self.filtered_file_data[orig_idx] == data) or \
                           (not use_filtered and self.file_data[orig_idx] == data):
                            original_idx = orig_idx
                            break
                    
                    # Cell border
                    self.canvas.create_rectangle(
                        current_x, current_y,
                        current_x + scaled_cell_width,
                        current_y + row_height,
                        outline="#cccccc", width=1
                    )
                    
                    # Draw content
                    if original_idx != -1:
                        self.draw_single_network(data, current_x, current_y, original_idx)
                        files_drawn += 1
                        
                        # Update UI every 5 files to prevent freezing
                        if files_drawn % 5 == 0:
                            self.root.update_idletasks()
                
                current_x += scaled_cell_width + scaled_padding
            
            current_y += row_height + scaled_padding
        
        # Update scroll region
        total_width = cols * (scaled_cell_width + scaled_padding) + scaled_padding
        total_height = current_y
        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))
    
    def draw_single_network(self, data, x_offset, y_offset, file_idx):
        """Draw one network with highlighting"""
        # Parameters with scale
        scaled_node_width = self.node_width * self.zoom_level
        scaled_node_height = self.node_height * self.zoom_level
        scaled_node_spacing = self.node_spacing * self.zoom_level
        scaled_column_distance = self.column_distance * self.zoom_level
        font_size = max(6, int(9 * self.zoom_level))
        
        # Column positions
        left_x = x_offset + 50 * self.zoom_level
        right_x = left_x + scaled_column_distance
        
        # File title
        title_font_size = max(8, int(10 * self.zoom_level))
        self.canvas.create_text(
            x_offset + self.cell_width * self.zoom_level // 2,
            y_offset + 10 * self.zoom_level,
            text=data['filename'],
            font=("Arial", title_font_size, "bold"),
            fill=self.text_color
        )
        
        # Frequency
        freq_font_size = max(10, int(14 * self.zoom_level))
        self.canvas.create_text(
            x_offset + self.cell_width * self.zoom_level // 2,
            y_offset + 25 * self.zoom_level,
            text=data['frequency'],
            font=("Arial", freq_font_size, "bold"),
            fill="#000000"
        )
        
        # Column headers
        header_font_size = max(8, int(12 * self.zoom_level))
        self.canvas.create_text(left_x + scaled_node_width // 2,
                               y_offset + 40 * self.zoom_level,
                               text="FROM", font=("Arial", header_font_size, "bold"))
        self.canvas.create_text(right_x + scaled_node_width // 2,
                               y_offset + 40 * self.zoom_level,
                               text="TO", font=("Arial", header_font_size, "bold"))
        
        # Skip drawing if no connections
        if not data['connections']:
            self.canvas.create_text(
                x_offset + self.cell_width * self.zoom_level // 2,
                y_offset + 80 * self.zoom_level,
                text="No data in date range",
                font=("Arial", int(10 * self.zoom_level)),
                fill="#999999"
            )
            return
        
        # Limit nodes for performance (top 50 each)
        max_nodes = 50
        from_nodes = sorted(data['from_counts'].keys(),
                          key=lambda x: data['from_counts'][x], reverse=True)[:max_nodes]
        to_nodes = sorted(data['to_counts'].keys(),
                        key=lambda x: data['to_counts'][x], reverse=True)[:max_nodes]
        
        if len(data['from_counts']) > max_nodes or len(data['to_counts']) > max_nodes:
            print(f"  Limiting to top {max_nodes} nodes for performance")
        
        # Node positions
        from_positions = {}
        to_positions = {}
        
        # FROM nodes
        y = y_offset + 60 * self.zoom_level
        for node in from_nodes:
            from_positions[node] = y
            y += scaled_node_height + scaled_node_spacing
        
        # TO nodes
        y = y_offset + 60 * self.zoom_level
        for node in to_nodes:
            to_positions[node] = y
            y += scaled_node_height + scaled_node_spacing
        
        # Debug: Print connection info
        total_connections = sum(data['connections'].values())
        max_conn = max(data['connections'].values()) if data['connections'] else 0
        print(f"File {file_idx}: max_conn={max_conn}, total_connections={total_connections}, unique_connections={len(data['connections'])}")
        
        # Check for data consistency
        if total_connections == 0:
            print(f"  WARNING: File {file_idx} has no connections!")
        elif max_conn == 0:
            print(f"  WARNING: File {file_idx} has max_conn=0!")
        
        # Get selected nodes for this file
        selected_from = self.selected_items.get(file_idx, {}).get('from', set())
        selected_to = self.selected_items.get(file_idx, {}).get('to', set())
        
        # Draw lines with highlighting (limit for performance)
        connections_to_draw = list(data['connections'].items())
        
        # For large networks, limit the number of lines drawn
        max_lines = 500  # Reduced to 500 lines for better performance
        if len(connections_to_draw) > max_lines:
            # Sort by count and take top connections
            connections_to_draw.sort(key=lambda x: x[1], reverse=True)
            connections_to_draw = connections_to_draw[:max_lines]
            print(f"  Limiting to top {max_lines} connections for performance")
        
        lines_drawn = 0
        for (from_node, to_node), count in connections_to_draw:
            if from_node in from_positions and to_node in to_positions:
                # Use absolute line width grading
                base_width = self.get_line_width_by_count(count)
                width = base_width * self.zoom_level
                
                # Debug: Print line info for first few connections
                if len(data['connections']) <= 5:  # Only for files with few connections
                    print(f"  Line {from_node}->{to_node}: count={count}, base_width={base_width}, final_width={width:.1f}")
                
                x1 = left_x + scaled_node_width
                y1 = from_positions[from_node] + scaled_node_height // 2
                x2 = right_x
                y2 = to_positions[to_node] + scaled_node_height // 2
                
                # Determine line color
                line_color = self.line_color
                if from_node in selected_from and to_node in selected_to:
                    line_color = self.highlight_line_color
                    # For selected lines, ensure minimum width of 2 pixels
                    width = max(width, 2 * self.zoom_level)
                
                self.canvas.create_line(x1, y1, x2, y2, 
                                       fill=line_color, width=width)
                lines_drawn += 1
                
                # Update UI every 50 lines for large networks
                if lines_drawn % 50 == 0:
                    self.root.update_idletasks()
        
        # Draw nodes
        for node, y in from_positions.items():
            self.draw_node(node, left_x, y, data['from_counts'][node], 
                         True, scaled_node_width, scaled_node_height, 
                         font_size, file_idx, node in selected_from)
        
        for node, y in to_positions.items():
            self.draw_node(node, right_x, y, data['to_counts'][node], 
                         False, scaled_node_width, scaled_node_height, 
                         font_size, file_idx, node in selected_to)
    
    def draw_node(self, node_id, x, y, count, is_from, width, height, font_size, file_idx, is_selected):
        """Draw node with highlighting"""
        formatted_id = str(node_id).rjust(8)
        
        # Background color depending on selection
        bg_color = self.selected_bg if is_selected else self.node_bg
        
        # Node rectangle
        rect = self.canvas.create_rectangle(x, y, x + width, y + height,
                                          fill=bg_color, outline=self.node_border,
                                          width=max(1, self.zoom_level),
                                          tags="node")
        
        # Save rectangle ID
        self.node_rectangles[(file_idx, node_id, is_from)] = rect
        
        # Node text
        text = self.canvas.create_text(x + width // 2, y + height // 2,
                                      text=formatted_id, font=("Courier", font_size),
                                      fill=self.text_color,
                                      tags="node")
        
        # Counter
        if is_from:
            count_text = self.canvas.create_text(x - 10 * self.zoom_level, y + height // 2,
                                                text=f"[{count}]", font=("Courier", font_size),
                                                fill=self.count_color, anchor="e",
                                                tags="node")
        else:
            count_text = self.canvas.create_text(x + width + 10 * self.zoom_level, y + height // 2,
                                                text=f"[{count}]", font=("Courier", font_size),
                                                fill=self.count_color, anchor="w",
                                                tags="node")
        
        # Mouse events
        for item in [rect, text, count_text]:
            self.canvas.tag_bind(item, "<Button-1>",
                               lambda e, nid=node_id, fidx=file_idx, is_f=is_from: 
                               self.on_node_left_click(nid, is_f, fidx))
            self.canvas.tag_bind(item, "<Button-3>",
                               lambda e, nid=node_id, fidx=file_idx, is_f=is_from: 
                               self.on_node_right_click(nid, is_f, fidx))
            self.canvas.tag_bind(item, "<Control-Button-1>",
                               lambda e, nid=node_id, fidx=file_idx, is_f=is_from: 
                               self.on_node_ctrl_click(nid, is_f, fidx))
    
    def on_node_left_click(self, node_id, is_from, file_idx):
        """Left click on node - select and copy connections"""
        # Stop canvas dragging when clicking on node
        self.canvas_drag_data["dragging"] = False
        
        # Clear selection for this file
        self.selected_items[file_idx]['from'].clear()
        self.selected_items[file_idx]['to'].clear()
        
        # Use filtered data if filter is applied
        data = self.filtered_file_data[file_idx] if len(self.filtered_file_data) > 0 else self.file_data[file_idx]
        
        if is_from:
            self.selected_items[file_idx]['from'].add(node_id)
            # Select all TO nodes connected to this FROM
            for (from_n, to_n), count in data['connections'].items():
                if from_n == node_id:
                    self.selected_items[file_idx]['to'].add(to_n)
        else:
            self.selected_items[file_idx]['to'].add(node_id)
            # Select all FROM nodes connected to this TO
            for (from_n, to_n), count in data['connections'].items():
                if to_n == node_id:
                    self.selected_items[file_idx]['from'].add(from_n)
        
        # Copy connections
        connections_text = self.get_selected_connections_text(file_idx)
        self.copy_to_clipboard(connections_text)
        
        # Redraw
        self.draw_all_networks()
    
    def on_node_right_click(self, node_id, is_from, file_idx):
        """Right click on node - same as left click"""
        self.on_node_left_click(node_id, is_from, file_idx)
    
    def on_node_ctrl_click(self, node_id, is_from, file_idx):
        """Ctrl+click on node - add to selection"""
        # Stop canvas dragging when clicking on node
        self.canvas_drag_data["dragging"] = False
        
        if is_from:
            if node_id in self.selected_items[file_idx]['from']:
                self.selected_items[file_idx]['from'].remove(node_id)
            else:
                self.selected_items[file_idx]['from'].add(node_id)
        else:
            if node_id in self.selected_items[file_idx]['to']:
                self.selected_items[file_idx]['to'].remove(node_id)
            else:
                self.selected_items[file_idx]['to'].add(node_id)
        
        # Copy connections if there is a selection
        if self.selected_items[file_idx]['from'] and self.selected_items[file_idx]['to']:
            connections_text = self.get_selected_connections_text(file_idx)
            self.copy_to_clipboard(connections_text)
        
        self.draw_all_networks()
    
    def get_selected_connections_text(self, file_idx):
        """Format selected connections (from working code)"""
        # Use filtered data if filter is applied
        data = self.filtered_file_data[file_idx] if len(self.filtered_file_data) > 0 else self.file_data[file_idx]
        selected_from = self.selected_items[file_idx]['from']
        selected_to = self.selected_items[file_idx]['to']
        
        lines = []
        lines.append("COUNT   FROM        TO          COUNT")
        lines.append("-" * 45)
        
        # If only one TO node selected
        if len(selected_to) == 1 and len(selected_from) > 0:
            to_node = list(selected_to)[0]
            
            selected_connections = []
            for (from_node, to_n), count in data['connections'].items():
                if to_n == to_node and from_node in selected_from:
                    selected_connections.append((from_node, to_n, count))
            
            selected_connections.sort(key=lambda x: (-x[2], x[0]))
            
            to_total = sum(count for _, _, count in selected_connections)
            
            for i, (from_node, to_n, count) in enumerate(selected_connections):
                from_str = str(from_node).rjust(8)
                to_str = str(to_n).rjust(8)
                count_str = str(count).ljust(6)
                
                if i == 0:
                    total_str = str(to_total).ljust(6)
                    lines.append(f"{count_str}  {from_str}    {to_str}    {total_str}")
                else:
                    lines.append(f"{count_str}  {from_str}    {''.ljust(8)}    ")
        else:
            selected_connections = []
            for (from_node, to_node), count in data['connections'].items():
                if from_node in selected_from and to_node in selected_to:
                    selected_connections.append((from_node, to_node, count))
            
            selected_connections.sort(key=lambda x: (x[0], x[1]))
            
            current_from = None
            from_total = 0
            from_connections = []
            
            for from_node, to_node, count in selected_connections:
                if from_node != current_from:
                    if current_from is not None:
                        for j, (fn, tn, cnt) in enumerate(from_connections):
                            fn_str = str(fn).rjust(8)
                            tn_str = str(tn).rjust(8)
                            cnt_str = str(cnt).ljust(6)
                            
                            if j == 0:
                                total_str = str(from_total).ljust(6)
                                lines.append(f"{total_str}  {fn_str}    {tn_str}    {cnt_str}")
                            else:
                                lines.append(f"{''.ljust(6)}  {''.ljust(8)}    {tn_str}    {cnt_str}")
                    
                    current_from = from_node
                    from_connections = [(from_node, to_node, count)]
                    from_total = count
                else:
                    from_connections.append((from_node, to_node, count))
                    from_total += count
            
            if current_from is not None:
                for j, (fn, tn, cnt) in enumerate(from_connections):
                    fn_str = str(fn).rjust(8)
                    tn_str = str(tn).rjust(8)
                    cnt_str = str(cnt).ljust(6)
                    
                    if j == 0:
                        total_str = str(from_total).ljust(6)
                        lines.append(f"{total_str}  {fn_str}    {tn_str}    {cnt_str}")
                    else:
                        lines.append(f"{''.ljust(6)}  {''.ljust(8)}    {tn_str}    {cnt_str}")
        
        return "\n".join(lines)
    
    def copy_to_clipboard(self, text):
        """Copy to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
    
    def zoom_in(self):
        """Increase zoom"""
        if self.zoom_level < self.max_zoom:
            self.zoom_level += self.zoom_step
            self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
            self.draw_all_networks()
    
    def zoom_out(self):
        """Decrease zoom"""
        if self.zoom_level > self.min_zoom:
            self.zoom_level -= self.zoom_step
            self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
            self.draw_all_networks()
    
    def zoom_reset(self):
        """Reset zoom"""
        self.zoom_level = 1.0
        self.zoom_label.config(text="100%")
        self.draw_all_networks()
    
    def refresh_all(self):
        """Refresh all data"""
        self.load_all_data()
        self.filtered_file_data = []
        
        # Update date range from new data
        self.set_date_range_from_data()
        
        # Update comboboxes
        self.update_comboboxes()
        
        self.filter_status.config(text="No filter applied", fg="#606060")
        self.draw_all_networks()
        
    def set_date_range_from_data(self):
        """Set date range based on loaded data"""
        min_date = None
        max_date = None
        
        # Search for minimum and maximum dates in all files
        for data in self.file_data:
            connection_dates = data.get('connection_dates', {})
            for dates_list in connection_dates.values():
                if dates_list:
                    for date in dates_list:
                        if date:
                            if min_date is None or date < min_date:
                                min_date = date
                            if max_date is None or date > max_date:
                                max_date = date
        
        # If dates found, set them
        if min_date and max_date:
            # Format dates to required format DD/MM/YY HH:MM:SS
            from_str = min_date.strftime("%d/%m/%y %H:%M:%S")
            to_str = max_date.strftime("%d/%m/%y %H:%M:%S")
            
            self.date_from_var.set(from_str)
            self.date_to_var.set(to_str)
            
            print(f"Date range from data: {from_str} to {to_str}")
        else:
            print("No dates found in data, using default range")


# MAIN() FUNCTION AT THE END
def main():
    root = tk.Tk()
    app = MultiFileNetworkVisualizer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    
    def parse_timestamp(self, timestamp_str):
        """Парсинг даты из формата YYYY:MM:DD:HH:MM:SS (формат из CSV)"""
        try:
            return datetime.strptime(timestamp_str, "%Y:%m:%d:%H:%M:%S")
        except:
            return None