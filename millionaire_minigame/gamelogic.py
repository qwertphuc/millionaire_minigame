import json
import random
from typing import Optional, Dict, List
from ai_support import GeminiAISupport

class MillionaireGame:
    def __init__(self, questions_file: str = 'questions.json', gemini_api_key: Optional[str] = None):
        self.questions_file = questions_file
        self.questions_db = self.load_questions()
        self.current_level = 1
        self.used_fifty_fifty = False
        self.used_change_question = False
        self.used_ai_support = False
        self.current_question = None
        self.removed_answers = []
        self.max_level = 8
        
        # Initialize AI Support (optional - will work without API key using fallback)
        self.ai_support = None
        try:
            self.ai_support = GeminiAISupport(api_key=gemini_api_key)
        except ValueError as e:
            print(f"Warning: AI Support initialized without Gemini API. Will use fallback mode.")
            print(f"To enable full AI support, set GEMINI_API_KEY environment variable.")

        
    def load_questions(self) -> List[Dict]:
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: {self.questions_file} not found!")
            return []
    
    def select_new_question(self) -> bool:
        level_questions = [q for q in self.questions_db if q['level'] == self.current_level]
        if level_questions:
            self.current_question = random.choice(level_questions)
            self.removed_answers = []
            return True
        else:
            print(f"Warning: No questions found for level {self.current_level}")
            return False
    
    def start_game(self) -> Dict:
        self.current_level = 1
        self.used_fifty_fifty = False
        self.used_change_question = False
        self.used_ai_support = False
        self.removed_answers = []
        self.select_new_question()
        return self.get_current_state()
    
    def get_current_state(self) -> Dict:
        """Get the current game state"""
        if not self.current_question:
            return {"error": "No question available"}
        
        return {
            "level": self.current_level,
            "question": self.current_question['question'],
            "answers": {
                1: self.current_question['answer1'],
                2: self.current_question['answer2'],
                3: self.current_question['answer3'],
                4: self.current_question['answer4']
            },
            "removed_answers": self.removed_answers,
            "supports": {
                "fifty_fifty": not self.used_fifty_fifty,
                "change_question": not self.used_change_question,
                "ai_support": not self.used_ai_support
            }
        }
    
    def check_answer(self, answer: int) -> Dict:
        """Check if the answer is correct"""
        if not self.current_question:
            return {"status": "error", "message": "Error: 0 question"}
        
        correct_answer = self.current_question['correct']
        
        if answer == correct_answer:
            if self.current_level >= self.max_level:
                return {
                    "status": "won",
                    "correct": True,
                    "message": "Won =)",
                    "correct_answer": correct_answer
                }
            else:
                self.current_level += 1
                self.select_new_question()
                return {
                    "status": "correct",
                    "correct": True,
                    "message": f"Correct! Moving to level {self.current_level}",
                    "correct_answer": correct_answer,
                    "new_state": self.get_current_state()
                }
        else:
            return {
                "status": "game_over",
                "correct": False,
                "message": "Wrong answer! Game Over.",
                "correct_answer": correct_answer,
                "your_answer": answer,
                "explanation": self.current_question['explanation']
            }
    
    def use_fifty_fifty(self) -> Dict:
        """Use 50/50 support - remove 2 wrong answers"""
        if self.used_fifty_fifty:
            return {"status": "error", "message": "50/50 used!"}
        
        self.used_fifty_fifty = True
        correct_answer = self.current_question['correct']
        
        # Get two wrong answers to remove
        wrong_answers = [i for i in [1, 2, 3, 4] if i != correct_answer]
        to_remove = random.sample(wrong_answers, 2)
        self.removed_answers = to_remove
        
        return {
            "status": "success",
            "message": "remove wrong answers.",
            "removed_answers": to_remove
        }
    
    def use_change_question(self) -> Dict:
        if self.used_change_question:
            return {"status": "error", "message": "Used!"}
        
        self.used_change_question = True
        self.select_new_question()
        
        return {
            "status": "success",
            "message": "Question changed!",
            "new_state": self.get_current_state()
        }
    
    def use_ai_support(self) -> Dict:
        """Use AI support - get explanation hint using Gemini AI"""
        if self.used_ai_support:
            return {"status": "error", "message": "AI support already used!"}
        
        self.used_ai_support = True
        explanation = self.current_question['explanation']
        
        # Try to use Gemini AI if available
        if self.ai_support:
            try:
                # Get AI-generated hint based on the explanation
                answers = {
                    1: self.current_question['answer1'],
                    2: self.current_question['answer2'],
                    3: self.current_question['answer3'],
                    4: self.current_question['answer4']
                }
                
                ai_hint = self.ai_support.get_ai_hint(
                    question=self.current_question['question'],
                    answers=answers,
                    explanation=explanation
                )
                
                ai_response = f"🤖 AI Assistant: {ai_hint}"
                
            except Exception as e:
                # Fallback to simple explanation if AI fails
                print(f"AI Support error: {e}")
                ai_response = self.ai_support.get_simple_hint(explanation)
        else:
            # Fallback mode without Gemini API
            sentences = explanation.split('. ')
            first_sentence = sentences[0] + '.' if sentences else explanation[:200]
            ai_response = f"💡 Hint: {first_sentence} Think carefully about this information."
        
        return {
            "status": "success",
            "message": "AI support activated!",
            "ai_response": ai_response
        }


def print_separator():
    """Print a visual separator"""
    print("\n" + "="*70 + "\n")


def print_question(state: Dict):
    """Display the current question and answers"""
    print_separator()
    print(f"LEVEL {state['level']}")
    print_separator()
    print(f"Question: {state['question']}\n")
    
    removed = state.get('removed_answers', [])
    answer_letters = ['A', 'B', 'C', 'D']
    
    for i in range(1, 5):
        if i in removed:
            print(f"  {answer_letters[i-1]}: [REMOVED]")
        else:
            print(f"  {answer_letters[i-1]}: {state['answers'][i]}")
    print()


def print_supports(state: Dict):
    """Display available support options"""
    supports = state['supports']
    print("Available Supports:")
    print(f"  1. 50/50 {'T' if supports['fifty_fifty'] else 'F (used)'}")
    print(f"  2. Change Question {'T' if supports['change_question'] else 'F (used)'}")
    print(f"  3. AI Support {'T' if supports['ai_support'] else 'F (used)'}")
    print()


def get_user_input(prompt: str, valid_options: List[str]) -> str:
    """Get validated user input"""
    while True:
        user_input = input(prompt).strip().upper()
        if user_input in valid_options:
            return user_input
        print(f"Invalid input! Please choose from: {', '.join(valid_options)}")


def play_terminal_game():
    """Main function to play the game in terminal"""
    print("="*70)
    print(" "*20 + "MILLIONAIRE GAME")
    print_separator()
    
    input("Press Enter to start the game...")
    
    # Initialize game
    game = MillionaireGame()
    game.start_game()
    
    # Game loop
    while True:
        state = game.get_current_state()
        print_question(state)
        print_supports(state)
        print("chose:")
        print("  A/B/C/D - Answer the question")
        print("  S - Use support")
        print("  Q - Quit game")
        
        action = get_user_input("\nYour choice: ", ['A', 'B', 'C', 'D', 'S', 'Q'])
        
        if action == 'Q':
            print("\nTerminal closed.")
            break
        
        elif action == 'S':
            # Support menu
            print("\nMENU")
            supports = state['supports']
            
            options = []
            if supports['fifty_fifty']:
                print("  1 - Use 50/50")
                options.append('1')
            if supports['change_question']:
                print("  2 - Change Question")
                options.append('2')
            if supports['ai_support']:
                print("  3 - AI Support")
                options.append('3')
            
            if not options:
                print("No supports available!")
                input("\nPress Enter to continue...")
                continue
            
            print("  B - Back to question")
            options.append('B')
            
            support_choice = get_user_input("\nChoose support: ", options)
            
            if support_choice == 'B':
                continue
            elif support_choice == '1':
                result = game.use_fifty_fifty()
                print(f"\n{result['message']}")
                if result['status'] == 'success':
                    print(f"Removed answers: {', '.join([chr(64+i) for i in result['removed_answers']])}")
                input("\nPress Enter to continue...")
            elif support_choice == '2':
                result = game.use_change_question()
                print(f"\n{result['message']}")
                input("\nPress Enter to continue...")
            elif support_choice == '3':
                result = game.use_ai_support()
                print(f"\n{result['message']}")
                if result['status'] == 'success':
                    print_separator()
                    print(result['ai_response'])
                    print_separator()
                input("\nPress Enter to continue...")
        
        else:
            # Answer the question
            answer_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
            answer_num = answer_map[action]
            
            # Check if answer is removed
            if answer_num in state.get('removed_answers', []):
                print("\nError: This answer has been removed by 50/50 support.")
                input("Press Enter to continue...")
                continue
            
            result = game.check_answer(answer_num)
            
            print_separator()
            if result['correct']:
                print(f"✓ {result['message']}")
                print(f"The correct answer was: {chr(64 + result['correct_answer'])}")
                
                if result['status'] == 'won':
                    print_separator()
                    print(" "*15 + "YOU WON THE GAME!")
                    print_separator()
                    break
                else:
                    input("\nPress Enter to next level...")
            else:
                print(f"✗ {result['message']}")
                print(f"Your answer: {chr(64 + result['your_answer'])}")
                print(f"Correct answer: {chr(64 + result['correct_answer'])}")
                print(f"\nExplanation: {result['explanation']}")
                print_separator()
                break
    
    # Ask to play again
    play_again = get_user_input("\nplay again? (Y/N): ", ['Y', 'N'])
    if play_again == 'Y':
        play_terminal_game()
    else:
        print("\nTerninal closed.")


if __name__ == "__main__":
    play_terminal_game()
