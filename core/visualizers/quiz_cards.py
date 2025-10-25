"""
Quiz Cards Generator - Interactive HTML cards for quiz questions
Each card shows the question, and reveals the answer when clicked
"""


def generate_quiz_cards_html(quiz_content: str, document_title: str, quiz_config: dict, logo_path: str = None) -> str:
    """
    Generate interactive HTML with flip cards for quiz questions.

    Args:
        quiz_content: The raw quiz text from LLM
        document_title: Document name
        quiz_config: Quiz configuration dict
        logo_path: Optional path to logo

    Returns:
        str: Complete HTML with interactive quiz cards
    """
    import base64
    from pathlib import Path

    # Encode logo if provided
    logo_uri = ""
    if logo_path and Path(logo_path).exists():
        try:
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode('utf-8')
                ext = Path(logo_path).suffix.lower()
                mime_type = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.svg': 'image/svg+xml'
                }.get(ext, 'image/png')
                logo_uri = f"data:{mime_type};base64,{logo_data}"
        except:
            pass

    if not logo_uri:
        logo_uri = """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 60'%3E%3Ctext x='10' y='40' font-family='Arial Black' font-size='32' fill='%2306b6d4'%3ESocrate AI%3C/text%3E%3C/svg%3E"""

    # Parse quiz content to extract questions and answers
    questions = parse_quiz_questions(quiz_content, quiz_config.get('type', 'mixed'))

    # Generate cards HTML
    cards_html = ""
    for i, q in enumerate(questions, 1):
        cards_html += generate_quiz_card(i, q['question'], q['answer'], q.get('type', 'generic'))

    # Get labels for config
    quiz_type_label = {
        'multiple_choice': 'Scelta Multipla',
        'true_false': 'Vero/Falso',
        'short_answer': 'Risposta Breve',
        'mixed': 'Misto'
    }.get(quiz_config.get('type', 'mixed'), 'Quiz')

    difficulty_label = {
        'easy': 'Facile',
        'medium': 'Medio',
        'hard': 'Difficile'
    }.get(quiz_config.get('difficulty', 'medium'), 'Medio')

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quiz Interattivo - {document_title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .header img {{
            height: 50px;
            margin-bottom: 15px;
        }}

        .header h1 {{
            color: #667eea;
            font-size: 2.2rem;
            margin-bottom: 10px;
        }}

        .header-meta {{
            color: #666;
            font-size: 1rem;
        }}

        .quiz-info {{
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .quiz-info h2 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}

        .quiz-info p {{
            color: #555;
            margin: 5px 0;
        }}

        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}

        .card {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            min-height: 250px;
            perspective: 1000px;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        }}

        .card-inner {{
            position: relative;
            width: 100%;
            height: 100%;
            min-height: 250px;
            text-align: center;
            transition: transform 0.6s;
            transform-style: preserve-3d;
        }}

        .card.flipped .card-inner {{
            transform: rotateY(180deg);
        }}

        .card-front, .card-back {{
            position: absolute;
            width: 100%;
            height: 100%;
            backface-visibility: hidden;
            border-radius: 15px;
            padding: 60px 30px 20px 30px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
            overflow-y: auto;
            overflow-x: hidden;
        }}

        .card-front {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        .card-back {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            transform: rotateY(180deg);
        }}

        .card-number {{
            position: absolute;
            top: 15px;
            left: 15px;
            background: rgba(255,255,255,0.2);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.1rem;
            z-index: 10;
        }}

        .card-type {{
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            z-index: 10;
        }}

        .question-text {{
            font-size: 1.1rem;
            font-weight: 600;
            line-height: 1.5;
            margin-bottom: 10px;
            max-width: 100%;
            word-wrap: break-word;
        }}

        .answer-text {{
            font-size: 1rem;
            line-height: 1.5;
            max-width: 100%;
            word-wrap: break-word;
        }}

        .tap-hint {{
            position: relative;
            width: 100%;
            text-align: center;
            font-size: 0.85rem;
            opacity: 0.8;
            font-style: italic;
            margin-top: 15px;
            flex-shrink: 0;
        }}

        .print-button {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: white;
            color: #667eea;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            transition: all 0.3s;
            z-index: 1000;
        }}

        .print-button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.4);
        }}

        @media print {{
            body {{
                background: white;
            }}

            .header {{
                border: 2px solid #667eea;
            }}

            .card {{
                break-inside: avoid;
                page-break-inside: avoid;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}

            .print-button {{
                display: none;
            }}

            .card-inner {{
                transform: none !important;
            }}

            .card-back {{
                position: relative;
                transform: none !important;
                margin-top: 10px;
                opacity: 0.7;
            }}

            .tap-hint {{
                display: none;
            }}
        }}

        @media (max-width: 768px) {{
            .cards-grid {{
                grid-template-columns: 1fr;
            }}

            .header h1 {{
                font-size: 1.5rem;
            }}

            .question-text {{
                font-size: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <button class="print-button" onclick="window.print()">🖨️ Stampa / PDF</button>

    <div class="container">
        <div class="header">
            <img src="{logo_uri}" alt="Logo">
            <h1>🎯 Quiz Interattivo</h1>
            <div class="header-meta">
                <strong>{document_title}</strong>
            </div>
        </div>

        <div class="quiz-info">
            <h2>📊 Informazioni Quiz</h2>
            <p><strong>Tipo:</strong> {quiz_type_label}</p>
            <p><strong>Difficoltà:</strong> {difficulty_label}</p>
            <p><strong>Numero domande:</strong> {len(questions)}</p>
            <p style="margin-top: 15px; font-style: italic; color: #667eea;">
                💡 Clicca su ogni card per vedere la risposta!
            </p>
        </div>

        <div class="cards-grid">
            {cards_html}
        </div>
    </div>

    <script>
        // Add click handlers to all cards
        document.querySelectorAll('.card').forEach(card => {{
            card.addEventListener('click', function() {{
                this.classList.toggle('flipped');
            }});
        }});
    </script>
</body>
</html>"""


def generate_quiz_card(number: int, question: str, answer: str, card_type: str = "generic") -> str:
    """Generate a single quiz card HTML."""
    type_icons = {
        'multiple_choice': '📝',
        'true_false': '✓/✗',
        'short_answer': '✍️',
        'generic': '❓'
    }

    icon = type_icons.get(card_type, '❓')

    return f"""
    <div class="card">
        <div class="card-inner">
            <div class="card-front">
                <div class="card-number">{number}</div>
                <div class="card-type">{icon}</div>
                <div class="question-text">{escape_html(question)}</div>
                <div class="tap-hint">👆 Clicca per vedere la risposta</div>
            </div>
            <div class="card-back">
                <div class="card-number">{number}</div>
                <div class="card-type">✅</div>
                <div class="answer-text">{escape_html(answer)}</div>
                <div class="tap-hint">👆 Clicca per tornare alla domanda</div>
            </div>
        </div>
    </div>"""


def parse_quiz_questions(quiz_text: str, quiz_type: str) -> list:
    """
    Parse quiz text to extract questions and answers.
    Handles the professional content_generators format with ## Domande and ## Risposte Corrette sections.
    """
    # Debug logging removed for production

    questions = []
    lines = quiz_text.split('\n')

    # Storage for parsing
    stored_questions = {}  # key: question_number, value: question_text
    stored_answers = {}    # key: question_number, value: answer_text

    current_section = None
    current_question_num = None
    current_text = []
    in_answers_section = False

    for line in lines:
        line_stripped = line.strip()

        # Skip empty lines and separators
        if not line_stripped or re.match(r'^[-=]{3,}$', line_stripped):
            continue

        # Detect section headers
        if re.match(r'^##\s+domande', line_stripped, re.IGNORECASE):
            current_section = 'questions'
            continue
        elif re.match(r'^##\s+risposte\s+corrette', line_stripped, re.IGNORECASE):
            # Save any pending question
            if current_section == 'questions' and current_question_num and current_text:
                stored_questions[current_question_num] = '\n'.join(current_text).strip()
            current_section = 'answers'
            in_answers_section = True
            current_question_num = None
            current_text = []
            continue

        # Skip main title (single #)
        if re.match(r'^#\s+[^#]', line_stripped):
            continue

        # Detect ### N. VERO o FALSO (compact format without "Domanda")
        match_compact = re.match(r'^###\s+(\d+)[\.\s]+(VERO\s+o\s+FALSO|vero\s+o\s+falso)', line_stripped, re.IGNORECASE)
        if match_compact:
            # Save previous question
            if current_question_num and current_text:
                stored_questions[current_question_num] = '\n'.join(current_text).strip()
            # Start new question
            current_question_num = int(match_compact.group(1))
            current_text = []
            if not current_section:
                current_section = 'questions'
            continue

        # Detect ### Domanda N (standard format)
        match = re.match(r'^###\s+domanda\s+(\d+)', line_stripped, re.IGNORECASE)
        if match:
            # Save previous question
            if current_question_num and current_text:
                stored_questions[current_question_num] = '\n'.join(current_text).strip()
            # Start new question
            current_question_num = int(match.group(1))
            current_text = []
            if not current_section:
                current_section = 'questions'
            continue

        # Detect answer lines: N. **Risposta corretta:** ...
        match_answer = re.match(r'^(\d+)\.\s*\*\*risposta\s+corretta:\*\*\s*(.+)', line_stripped, re.IGNORECASE)
        if match_answer:
            # Save any pending question
            if current_section == 'questions' and current_question_num and current_text:
                stored_questions[current_question_num] = '\n'.join(current_text).strip()
                current_text = []

            # Switch to answers section
            if not in_answers_section:
                current_section = 'answers'
                in_answers_section = True

            # Store the answer directly
            answer_num = int(match_answer.group(1))
            answer_text = match_answer.group(2).strip()
            stored_answers[answer_num] = answer_text
            current_question_num = None
            continue

        # Parse based on current section
        if current_section == 'questions' and current_question_num:
            # Accumulate question text (including options A, B, C, D)
            current_text.append(line_stripped)
        elif current_section == 'answers':
            # Detect numbered answer (1. or 1) at start of line) - old format
            match_old = re.match(r'^(\d+)[\.\)]\s*$', line_stripped)
            if match_old:
                # Save previous answer
                if current_question_num and current_text:
                    stored_answers[current_question_num] = '\n'.join(current_text).strip()
                # Start new answer
                current_question_num = int(match_old.group(1))
                current_text = []
                continue

            # Collect answer text, stop at **Spiegazione:**
            if current_question_num:
                if re.match(r'^\*\*spiegazione:\*\*', line_stripped, re.IGNORECASE):
                    # Stop collecting - we don't want explanations
                    continue

                # Remove **Risposta corretta:** prefix if present
                if re.match(r'^\*\*risposta\s+corretta:\*\*', line_stripped, re.IGNORECASE):
                    line_stripped = re.sub(r'^\*\*risposta\s+corretta:\*\*\s*', '', line_stripped, flags=re.IGNORECASE)

                if line_stripped:
                    current_text.append(line_stripped)

    # Save last pending answer
    if current_section == 'answers' and current_question_num and current_text:
        stored_answers[current_question_num] = '\n'.join(current_text).strip()

    # Save last pending question if still in questions section
    if current_section == 'questions' and current_question_num and current_text:
        stored_questions[current_question_num] = '\n'.join(current_text).strip()

    # Match questions with answers
    # If no answers were found but we have questions, try to extract answers from questions
    if not stored_answers and stored_questions and quiz_type == 'true_false':
        for num, question_text in stored_questions.items():
            # For True/False questions, look for patterns like:
            # - Lines starting with "Risposta:" or "**Risposta:**"
            # - Or just assume "Vero" if not found (placeholder)
            lines_q = question_text.split('\n')
            answer_found = None
            question_lines = []

            for line in lines_q:
                # Check if this line contains the answer
                if re.match(r'^\*?\*?risposta:?\*?\*?', line.strip(), re.IGNORECASE):
                    answer_found = re.sub(r'^\*?\*?risposta:?\*?\*?\s*', '', line.strip(), flags=re.IGNORECASE)
                elif re.match(r'^(vero|falso)', line.strip(), re.IGNORECASE) and len(line.strip()) < 20:
                    # Short line starting with vero/falso might be the answer
                    if not answer_found:
                        answer_found = line.strip()
                else:
                    question_lines.append(line)

            if answer_found:
                stored_answers[num] = answer_found
                # Update question without the answer line
                stored_questions[num] = '\n'.join(question_lines).strip()

    for num in sorted(stored_questions.keys()):
        if num in stored_answers:
            questions.append({
                'question': stored_questions[num],
                'answer': stored_answers[num],
                'type': quiz_type
            })

    return questions


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    import html
    return html.escape(text)


# For testing
import re

if __name__ == "__main__":
    sample_quiz = """
1. Qual è la Legge del Tre secondo Gurdjieff?

Risposta: La Legge del Tre afferma che ogni fenomeno è il risultato di tre forze: attiva, passiva e neutralizzante. Nessun fenomeno può verificarsi senza l'azione combinata di queste tre forze.

2. Quanti centri ha l'uomo secondo l'insegnamento?

R: L'uomo ha sette centri: intellettuale, emozionale, motorio, istintivo, sessuale, superiore emozionale e superiore intellettuale.
    """

    config = {
        'type': 'mixed',
        'difficulty': 'medium',
        'num_questions': 2
    }

    html = generate_quiz_cards_html(sample_quiz, "Test Document", config)
    with open("test_quiz.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Test HTML generated!")
