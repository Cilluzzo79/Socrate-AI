"""
Test script to extract and save the full quiz text from the latest generation.
This will help us understand the exact format the LLM is using.
"""

# Based on the debug output, the quiz is 2369 characters and 40 lines
# The first 500 chars show it's in the format:
# # Quiz: La Legge del Tre secondo l'Insegnamento di Gurdjieff
#
# ## Istruzioni
# Leggi attentamente le seguenti affermazioni sulla Legge del Tre e determina se sono vere o false.
#
# ## Domande
#
# ### Domanda 1
# VERO O FALSO: La Legge del Tre stabilisce che ogni azione nell'universo è il risultato dell'interazione di due forze opposte: positiva e negativa.
#
# ### Domanda 2
# VERO O FALSO: La Legge del Tre è considerata una delle due leggi fondamentali dell'universo, insieme alla Legge del Sette o Legge dell'Ot

# Let's temporarily modify the parser to save the full quiz text to a file
import os

def save_quiz_for_analysis(quiz_text: str):
    """Save the quiz text to Desktop for analysis"""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    filepath = os.path.join(desktop, "quiz_analysis.txt")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"=== QUIZ TEXT ({len(quiz_text)} chars, {len(quiz_text.splitlines())} lines) ===\n\n")
        f.write(quiz_text)
        f.write("\n\n=== END QUIZ TEXT ===\n")

    print(f"Saved quiz to: {filepath}")
    return filepath

# Test with the partial quiz we have
partial_quiz = """# Quiz: La Legge del Tre secondo l'Insegnamento di Gurdjieff

## Istruzioni
Leggi attentamente le seguenti affermazioni sulla Legge del Tre e determina se sono vere o false.

## Domande

### Domanda 1
VERO O FALSO: La Legge del Tre stabilisce che ogni azione nell'universo è il risultato dell'interazione di due forze opposte: positiva e negativa.

### Domanda 2
VERO O FALSO: La Legge del Tre è considerata una delle due leggi fondamentali dell'universo, insieme alla Legge del Sette o Legge dell'Ot"""

if __name__ == "__main__":
    save_quiz_for_analysis(partial_quiz)
    print("\n[ANALYSIS]")
    print("The quiz format shows it's using 'VERO O FALSO:' inline with questions.")
    print("There's NO separate '## Risposte Corrette' section.")
    print("\nFor True/False quizzes, the LLM likely embeds answers directly after each question,")
    print("or includes them at the end in a different format than the parser expects.")
