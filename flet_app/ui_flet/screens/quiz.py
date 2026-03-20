import flet as ft
import asyncio
import logging
from core.quiz_engine import QuizEngine
from typing import Callable, Optional
from flet_app.ui_flet.theme import palette

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def QuizScreen(page: ft.Page, quiz_engine: QuizEngine, on_complete: Callable, debug_report: Optional[Callable[..., None]] = None, show_animations: bool = True, fps: int = 60):
    colors = palette(page)
    
    logger.info(f"[QuizScreen] Initializing - engine has {len(quiz_engine.questions) if hasattr(quiz_engine, 'questions') else 0} questions, current_idx={quiz_engine.current_idx if hasattr(quiz_engine, 'current_idx') else 'N/A'}")
    if debug_report:
        debug_report("quiz_screen_init", questions_count=len(quiz_engine.questions) if hasattr(quiz_engine, 'questions') else 0, current_idx=quiz_engine.current_idx if hasattr(quiz_engine, 'current_idx') else 0)
    
    # Progress UI
    progress_text = ft.Text("Question 1", size=14, weight=ft.FontWeight.BOLD, color=colors["muted"])
    timer_bar = ft.ProgressBar(
        width=600,
        color=colors["primary"],
        bgcolor=colors["card_border"],
        value=1.0,
    )
    timer_label = ft.Text("Time: 10s", size=12, color=colors["muted"])
    
    # State tracking
    timer_running = [False]
    is_active = [True]
    timer_task = [None]
    advance_task = [None]
    
    word_text = ft.Text("", size=48, weight=ft.FontWeight.BOLD, color=colors["text"])

    # Feedback Drawer (Slides up from bottom - less intrusive)
    feedback_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, size=24)
    feedback_title = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
    feedback_subtitle = ft.Text("", size=14)
    
    # Build feedback drawer with conditional animations - smaller height
    feedback_drawer_kwargs = {
        "content": ft.Row([
            ft.Container(width=20), # Smaller spacer
            feedback_icon,
            ft.Container(width=10),
            ft.Column([
                feedback_title,
                feedback_subtitle
            ], tight=True, spacing=2),
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        "height": 80,  # Reduced height
        "bgcolor": colors["success"], # Default to success
        "padding": 15,
        "offset": ft.Offset(0, 1), # Hidden initially (1 unit down = 100% of height)
        "visible": False,  # Start hidden to prevent blocking
    }
    if show_animations:
        # Fluidity-focused: Smooth slide animation
        feedback_drawer_kwargs["animate_offset"] = ft.Animation(300, ft.AnimationCurve.EASE_OUT)
    
    feedback_drawer = ft.Container(**feedback_drawer_kwargs)

    def cleanup():
        if debug_report:
            debug_report("quiz_cleanup")
        is_active[0] = False
        timer_running[0] = False
        quiz_engine.timer_running = False
        if timer_task[0]:
            timer_task[0].cancel()
        if advance_task[0]:
            advance_task[0].cancel()
        # Clean up keyboard event handler
        page.on_keyboard_event = None

    async def update_timer():
        if not is_active[0]: return
        if quiz_engine.word_time_limit <= 0:
            timer_bar.value = 1.0
            timer_label.value = "∞"
            page.update()
            return

        # Fluidity-focused: Use FPS setting for smooth updates
        # 60 FPS = 16.67ms, 120 FPS = 8.33ms
        update_interval = 1.0 / fps  # Dynamic based on FPS setting
        
        while timer_running[0] and is_active[0]:
            try:
                # Accumulate time for accurate timer tracking
                time_up = quiz_engine.timer_tick(int(update_interval * 1000))
                progress = quiz_engine.get_timer_progress()
                time_left = max(0, (quiz_engine.word_time_left_ms + 999) // 1000)

                timer_bar.value = progress
                timer_label.value = f"Time: {time_left}s"
                
                if progress > 0.5: timer_bar.color = colors["primary"]
                elif progress > 0.25: timer_bar.color = colors["warning"]
                else: timer_bar.color = colors["danger"]

                page.update()

                if time_up or progress <= 0:
                    timer_running[0] = False
                    if is_active[0] and not quiz_engine.is_waiting_for_next:
                        # Use create_task instead of run_task to properly handle async function
                        asyncio.create_task(check_answer(None, True))
                    break

                await asyncio.sleep(update_interval)
                if not quiz_engine.timer_running or quiz_engine.is_waiting_for_next:
                    break
            except asyncio.CancelledError:
                break
            except Exception:
                break

    def start_timer():
        if not is_active[0]: return
        if timer_task[0]: timer_task[0].cancel()
        quiz_engine.timer_running = True
        if quiz_engine.word_time_limit <= 0:
            timer_running[0] = False
            timer_bar.value = 1.0
            page.update()
            return
        timer_running[0] = True
        timer_task[0] = page.run_task(update_timer)

    # Question Card with Animations
    card_kwargs = {
        "content": word_text,
        "alignment": ft.Alignment(0, 0),
        "width": 600,
        "height": 300,
        "bgcolor": colors["card_bg"],
        "border_radius": 20,
        "border": ft.border.all(2, colors["card_border"]),
        "shadow": ft.BoxShadow(blur_radius=30, color="#00000014", offset=ft.Offset(0, 10)),
    }
    if show_animations:
        # Fluidity-focused: Use smooth curves with longer durations for continuous motion
        # EASE_OUT provides smooth, natural deceleration
        card_kwargs["animate_scale"] = ft.Animation(400, ft.AnimationCurve.EASE_OUT)
        card_kwargs["animate_offset"] = ft.Animation(300, ft.AnimationCurve.EASE_OUT)
    
    card = ft.Container(**card_kwargs)

    answer_input = ft.TextField(
        hint_text="Type answer here...",
        text_align=ft.TextAlign.CENTER,
        text_size=24,
        autofocus=True,
        read_only=True,  # Must be True - keyboard handler processes input, not native input
        autocorrect=False,
        enable_suggestions=False,
        height=80,
        border_radius=15,
        width=600,
        color=colors["text"],
        border_color=colors["card_border"],
        bgcolor=colors["card_alt_bg"],
    )

    def show_feedback_drawer(is_correct: bool, correct_word: str):
        if is_correct:
            feedback_drawer.bgcolor = "#D7FFB8" if page.theme_mode == ft.ThemeMode.LIGHT else "#233614"
            feedback_icon.icon = ft.Icons.CHECK_CIRCLE
            feedback_icon.color = "#58A700"
            feedback_title.value = "Excellent!"
            feedback_title.color = "#58A700"
            feedback_subtitle.value = f"'{correct_word}' is correct."
            feedback_subtitle.color = "#58A700"
        else:
            feedback_drawer.bgcolor = "#FFDFE0" if page.theme_mode == ft.ThemeMode.LIGHT else "#4A1A1C"
            feedback_icon.icon = ft.Icons.CANCEL
            feedback_icon.color = "#EA2B2B"
            feedback_title.value = "Correct Answer:"
            feedback_title.color = "#EA2B2B"
            feedback_subtitle.value = correct_word
            feedback_subtitle.color = "#EA2B2B"
        
        feedback_drawer.visible = True
        feedback_drawer.offset = ft.Offset(0, 0)
        page.update()

    def hide_feedback_drawer():
        feedback_drawer.visible = False
        feedback_drawer.offset = ft.Offset(0, 1)
        page.update()

    async def shake_card():
        if not show_animations: return
        # Quick shake sequence
        for off in [0.02, -0.02, 0.01, -0.01, 0]:
            card.offset = ft.Offset(off, 0)
            page.update()
            await asyncio.sleep(0.05)

    def show_current_question():
        if not is_active[0]: return
        
        logger.info(f"[show_current_question] current_idx={quiz_engine.current_idx}, questions_count={len(quiz_engine.questions) if hasattr(quiz_engine, 'questions') and quiz_engine.questions else 0}")
        if debug_report:
            debug_report("show_current_question", current_idx=quiz_engine.current_idx, questions_count=len(quiz_engine.questions) if hasattr(quiz_engine, 'questions') and quiz_engine.questions else 0)
        
        # Safety check - make sure we have questions
        if not hasattr(quiz_engine, 'questions') or not quiz_engine.questions:
            logger.error("No questions available in quiz engine")
            if debug_report:
                debug_report("quiz_no_questions_error")
            on_complete()
            return
            
        if quiz_engine.current_idx >= len(quiz_engine.questions):
            logger.info(f"[show_current_question] No more questions, current_idx={quiz_engine.current_idx}, len={len(quiz_engine.questions)}")
            on_complete()
            return

        hide_feedback_drawer()
        
        try:
            chi, _ = quiz_engine.get_current_word()
            current, total = quiz_engine.get_progress()
            logger.info(f"[show_current_question] Displaying question {current}/{total}: '{chi}'")
        except Exception as e:
            logger.error(f"Error getting current question: {e}")
            if debug_report:
                debug_report("quiz_question_error", error=str(e))
            on_complete()
            return

        # Reset card
        card.scale = 1.0
        card.bgcolor = colors["card_bg"]
        word_text.value = chi or "Loading..."
        word_text.color = colors["text"]

        progress_text.value = f"Question {current} of {total}"
        answer_input.value = ""
        answer_input.disabled = False
        
        # Single page update for better performance
        page.update()
        
        # Ensure focus after UI reset
        answer_input.focus()
        
        start_timer()
        logger.info(f"[show_current_question] Timer started, question displayed")

    async def skip_question(e=None):
        if not is_active[0] or quiz_engine.is_waiting_for_next: return
        
        timer_running[0] = False
        result = quiz_engine.check_answer("", skipped=True)
        answer_input.disabled = True
        
        show_feedback_drawer(False, result['correct'])
        
        await asyncio.sleep(1.2)  # Reduced from 2.0 to 1.2 seconds
        advance_to_next()

    async def check_answer(e, is_timeout: bool = False):
        if not is_active[0] or quiz_engine.is_waiting_for_next: return
        
        # If empty and not timeout, treat as skip
        if not answer_input.value and not is_timeout:
            await skip_question()
            return

        timer_running[0] = False
        result = quiz_engine.check_answer(answer_input.value or "", is_timeout=is_timeout)
        if result.get("status") == "invalid": return
        
        answer_input.disabled = True
        
        if result.get('is_correct', False):
            if show_animations:
                card.scale = 1.1 # Elastic pop
            page.update()
        else:
            if show_animations:
                await shake_card() # Shake
            
        show_feedback_drawer(result.get('is_correct', False), result.get('correct', '???'))
        
        # Advance after delay - reduced from 2.0 to 1.2 seconds
        await asyncio.sleep(1.2)
        advance_to_next()

    def advance_to_next():
        if not is_active[0]: return
        if not quiz_engine.next_question():
            on_complete()
        else:
            show_current_question()

    # Layout
    main_content = ft.Column([
        progress_text,
        timer_bar,
        ft.Row([timer_label], alignment=ft.MainAxisAlignment.END, width=600),
        ft.Container(height=20),
        card,
        ft.Container(height=40),
        answer_input,
        ft.Row([
            ft.ElevatedButton(
                "CHECK ANSWER",
                style=ft.ButtonStyle(
                    color=colors["primary_text"],
                    bgcolor=colors["primary"],
                    padding=25,
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
                expand=True,
                on_click=check_answer
            ),
            ft.ElevatedButton(
                "SKIP",
                style=ft.ButtonStyle(
                    color=colors["text"],
                    bgcolor=colors["card_alt_bg"],
                    padding=25,
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
                width=150,
                on_click=skip_question
            ),
        ], width=600, spacing=10),
        ft.Container(height=100),  # Add padding at bottom to prevent feedback drawer blocking
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

    # Wrap main_content in a container that fills space but leaves room for drawer
    main_container = ft.Container(
        content=main_content,
        expand=True,
        alignment=ft.alignment.Alignment(0, 0),
    )

    # Stack with drawer using visible property to prevent blocking when hidden
    root_stack = ft.Stack([
        main_container,
        feedback_drawer,  # Direct placement - will be positioned by its offset
    ], expand=True)

    # Global keyboard handler to capture input even when TextField isn't focused
    async def handle_page_key_event(e):
        if not is_active[0] or answer_input.disabled: return
        if e.key == "Enter":
            await check_answer(None)
        elif e.key == "Backspace":
            answer_input.value = (answer_input.value or "")[:-1]
            page.update()
        elif len(e.key) == 1:
            # Preserve case when Shift is pressed, otherwise convert to lowercase
            # e.key returns uppercase for letters, so we check e.shift to preserve case
            char = e.key.lower() if not e.shift else e.key
            answer_input.value = (answer_input.value or "") + char
            page.update()

    page.on_keyboard_event = handle_page_key_event
    
    container = ft.Container(content=root_stack, expand=True)
    container.cleanup = cleanup
    
    # Use a deferred task to start the quiz after UI is ready
    def deferred_start():
        logger.info("[QuizScreen] Starting quiz with deferred call")
        if debug_report:
            debug_report("quiz_deferred_start")
        show_current_question()
    
    container.start = deferred_start
    return container
