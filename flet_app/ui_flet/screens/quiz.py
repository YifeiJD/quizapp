import flet as ft
import asyncio
import logging
from core.quiz_engine import QuizEngine
from typing import Callable, Optional
from flet_app.ui_flet.theme import palette

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def QuizScreen(page: ft.Page, quiz_engine: QuizEngine, on_complete: Callable, debug_report: Optional[Callable[..., None]] = None):
    colors = palette(page)
    progress_text = ft.Text("Question 1", size=14, weight=ft.FontWeight.BOLD, color=colors["muted"])
    word_text = ft.Text("", size=48, weight=ft.FontWeight.BOLD, color=colors["text"])
    
    # Timer bar
    timer_bar = ft.ProgressBar(
        width=600,
        color=colors["primary"],
        bgcolor=colors["card_border"],
        value=1.0
    )
    timer_label = ft.Text("Time: 10s", size=12, color=colors["muted"])
    timer_status = ft.Text("Timer: stopped", size=12, color=colors["muted"])
    
    # Timer update function
    timer_running = [False]
    is_active = [True]
    timer_task = [None]
    advance_task = [None]

    def cleanup():
        """Stop background work when leaving the quiz screen."""
        if debug_report:
            debug_report("quiz_cleanup")
        is_active[0] = False
        timer_running[0] = False
        quiz_engine.timer_running = False
        if timer_task[0]:
            timer_task[0].cancel()
            timer_task[0] = None
        if advance_task[0]:
            advance_task[0].cancel()
            advance_task[0] = None

    async def update_timer():
        """Update timer bar on Flet's event loop."""
        logger.debug(f"[TIMER] Thread started, time_limit={quiz_engine.word_time_limit}")
        if debug_report:
            debug_report("quiz_timer_started", time_limit=quiz_engine.word_time_limit)

        if not is_active[0]:
            return

        if quiz_engine.word_time_limit <= 0:
            # No timer, show full bar
            timer_bar.value = 1.0
            timer_label.value = "∞"
            page.update()
            logger.debug("[TIMER] No time limit, showing infinity")
            return

        while timer_running[0] and is_active[0]:
            try:
                time_up = quiz_engine.timer_tick(100)
                progress = quiz_engine.get_timer_progress()
                time_left_ms = quiz_engine.word_time_left_ms
                time_left = max(0, (time_left_ms + 999) // 1000)

                logger.debug(f"[TIMER] time_left_ms={time_left_ms}, progress={progress}")
                timer_bar.value = progress
                timer_label.value = f"Time: {time_left}s"
                timer_status.value = "Timer: running"
                if debug_report:
                    debug_report("quiz_timer_tick", progress=progress, time_left=time_left, idx=quiz_engine.current_idx)

                if progress > 0.5:
                    timer_bar.color = colors["primary"]
                elif progress > 0.25:
                    timer_bar.color = colors["warning"]
                else:
                    timer_bar.color = colors["danger"]

                page.update()

                # Check if time is up - auto submit the answer
                if time_up or progress <= 0:
                    logger.debug("[TIMER] Time's up! Auto-submitting answer...")
                    timer_running[0] = False
                    quiz_engine.timer_running = False
                    timer_status.value = "Timer: timed out"
                    if is_active[0] and not quiz_engine.is_waiting_for_next:
                        if debug_report:
                            debug_report("quiz_timer_timeout")
                        check_answer(None, is_timeout=True)
                    break

                await asyncio.sleep(0.1)
                if not quiz_engine.timer_running or quiz_engine.is_waiting_for_next:
                    break
            except asyncio.CancelledError:
                logger.debug("[TIMER] Timer task cancelled")
                break
            except Exception as e:
                logger.error(f"[TIMER] Error in timer thread: {e}")
                break

        logger.debug("[TIMER] Thread ended")

    def start_timer():
        if not is_active[0]:
            return
        if timer_task[0]:
            timer_task[0].cancel()
            timer_task[0] = None
        quiz_engine.timer_running = True
        if quiz_engine.word_time_limit <= 0:
            if debug_report:
                debug_report("quiz_timer_disabled")
            timer_running[0] = False
            timer_bar.value = 1.0
            timer_label.value = "∞"
            timer_status.value = "Timer: off"
            page.update()
            return

        timer_running[0] = True
        timer_task[0] = page.run_task(update_timer)

    async def delayed_advance():
        try:
            await asyncio.sleep(1.5)
            if not is_active[0]:
                return
            advance_to_next_question()
            logger.debug("[QUIZ] Delayed next completed")
        except asyncio.CancelledError:
            logger.debug("[QUIZ] Delayed next cancelled")

    def schedule_next_question():
        """Advance after feedback unless the screen has been cleaned up."""
        if debug_report:
            debug_report("quiz_schedule_next")
        if advance_task[0]:
            advance_task[0].cancel()
        advance_task[0] = page.run_task(delayed_advance)
    
    # The Flashcard Container with Built-in Animations
    card = ft.Container(
        content=word_text,
        alignment=ft.alignment.Alignment(0, 0),
        width=600,
        height=300,
        bgcolor=colors["card_bg"],
        border_radius=20,
        border=ft.border.all(2, colors["card_border"]),
        shadow=ft.BoxShadow(blur_radius=20, color="#0000001F"),
        # Here is where the magic happens:
        animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
    )

    answer_input = ft.TextField(
        hint_text="Type answer here...", 
        text_align=ft.TextAlign.CENTER,
        text_size=20,
        autofocus=True,
        read_only=True,
        capitalization=ft.TextCapitalization.NONE,
        autocorrect=False,
        enable_suggestions=False,
        smart_dashes_type=False,
        smart_quotes_type=False,
        height=70,
        border_radius=10,
        width=600,
        color=colors["text"],
        border_color=colors["card_border"],
        bgcolor=colors["card_alt_bg"],
    )

    async def focus_answer_input():
        await asyncio.sleep(0)
        if not is_active[0] or answer_input.disabled:
            return
        try:
            answer_input.focus()
            page.update()
        except Exception:
            pass
    
    def skip_question():
        """Skip the current question."""
        logger.debug("[SKIP] Skipping question...")
        if debug_report:
            debug_report("quiz_skip_attempt", idx=quiz_engine.current_idx)
        if not is_active[0] or quiz_engine.is_waiting_for_next:
            return
        
        # Stop the timer thread when skipping
        timer_running[0] = False
        quiz_engine.timer_running = False
        
        result = quiz_engine.check_answer("", skipped=True)
        logger.debug(f"[SKIP] Result: {result}")
        if debug_report:
            debug_report("quiz_skip_result", result=result)
        if result.get("status") == "invalid":
            return
        
        # Animate feedback for skipped question
        card.bgcolor = colors["muted"]
        card.scale = 1.0
            
        word_text.value = result['correct']
        word_text.color = "#FFFFFF"
        answer_input.disabled = True
        page.update()
        
        # Auto advance to next question
        logger.debug("[SKIP] Scheduling next question in 1.5s")
        schedule_next_question()

    def show_current_question():
        if not is_active[0]:
            return
        if quiz_engine.current_idx >= len(quiz_engine.questions):
            timer_running[0] = False
            quiz_engine.timer_running = False
            on_complete()
            return

        chi, _ = quiz_engine.get_current_word()
        current, total = quiz_engine.get_progress()

        # Reset card
        card.bgcolor = colors["card_bg"]
        card.scale = 1.0
        word_text.value = chi
        word_text.color = colors["text"]

        # Reset timer
        if quiz_engine.word_time_limit > 0:
            timer_bar.value = 1.0
            timer_label.value = f"Time: {quiz_engine.word_time_limit}s"
            timer_status.value = "Timer: running"
        else:
            timer_bar.value = 1.0
            timer_label.value = "∞"
            timer_status.value = "Timer: off"

        progress_text.value = f"Question {current} of {total}"
        if debug_report:
            debug_report("quiz_show_question", current=current, total=total, prompt=chi)
        answer_input.value = ""
        answer_input.disabled = False
        page.update()
        page.run_task(focus_answer_input)

        # Start timer for this question
        start_timer()

    def advance_to_next_question():
        if not is_active[0]:
            return
        advance_task[0] = None
        if debug_report:
            debug_report("quiz_advance_next", next_idx=quiz_engine.current_idx + 1)
        if not quiz_engine.next_question():
            timer_running[0] = False
            quiz_engine.timer_running = False
            on_complete()
            return
        show_current_question()

    def check_answer(e, is_timeout: bool = False):
        logger.debug(f"[CHECK_ANSWER] Event handler started, is_timeout={is_timeout}")
        if debug_report:
            debug_report("quiz_check_answer_attempt", is_timeout=is_timeout, raw_value=answer_input.value or "", idx=quiz_engine.current_idx)
        if not is_active[0] or quiz_engine.is_waiting_for_next:
            logger.debug("[CHECK_ANSWER] Screen inactive or waiting for next question")
            return

        if not answer_input.value and not is_timeout:
            logger.debug("[CHECK_ANSWER] No input, returning early")
            return

        # Stop the timer thread when checking answer
        timer_running[0] = False
        quiz_engine.timer_running = False

        result = quiz_engine.check_answer(answer_input.value if answer_input.value else "", is_timeout=is_timeout)
        if debug_report:
            debug_report("quiz_check_answer_result", result=result)
        if result.get("status") == "invalid":
            logger.debug("[CHECK_ANSWER] Invalid result received, returning")
            return
        logger.debug(f"[CHECK_ANSWER] Result: is_correct={result['is_correct']}, correct={result['correct']}")
        
        # Animate feedback!
        if result['is_correct']:
            card.bgcolor = colors["success"]
            card.scale = 1.05 # Slight pop effect
        else:
            card.bgcolor = colors["danger"]
            card.scale = 0.95 # Slight shrink effect
            
        word_text.value = result['correct']
        word_text.color = "#FFFFFF"
        answer_input.disabled = True
        page.update()
        
        # Use threading.Timer instead of blocking time.sleep() to avoid freezing UI
        logger.debug("[CHECK_ANSWER] Scheduling next question in 1.5s")
        schedule_next_question()
        
        logger.debug("[CHECK_ANSWER] Event handler completed")

    def handle_submit(e):
        """Handle Enter key or submit button click."""
        logger.debug(f"[ENTER_KEY] handle_submit called, input='{answer_input.value}'")
        if answer_input.value.strip():
            # If there's text, submit the answer
            logger.debug("[ENTER_KEY] Text found, submitting answer")
            check_answer(e)
        else:
            # If empty, skip the question
            logger.debug("[ENTER_KEY] Empty field, skipping question")
            skip_question()

    # Set up Enter key handler
    answer_input.on_submit = handle_submit

    def handle_check_button(e):
        """Handle Check Answer button click - use same logic as Enter key."""
        if answer_input.value.strip():
            # If there's text, submit the answer
            logger.debug("[CHECK_BTN] Text found, submitting answer")
            check_answer(e)
        else:
            # If empty, skip the question
            logger.debug("[CHECK_BTN] Empty field, skipping question")
            skip_question()

    def handle_skip_button(e):
        """Handle skip button click."""
        skip_question()

    submit_btn = ft.ElevatedButton(
        "Check Answer",
        height=50,
        width=270,
        on_click=handle_check_button
    )
    skip_btn = ft.ElevatedButton(
        "Skip Question",
        height=50,
        width=270,
        bgcolor=colors["muted"],
        color=colors["primary_text"],
        on_click=handle_skip_button
    )

    def handle_page_key_event(e):
        """Handle keyboard events at page level."""
        if not is_active[0] or answer_input.disabled:
            return

        if e.key == "Enter":
            logger.debug("[PAGE_KEY] Enter pressed at page level")
            e.data = ""  # Prevent default beep sound
            handle_submit(None)
            return

        if e.key == "Backspace":
            answer_input.value = (answer_input.value or "")[:-1]
            page.update()
            return

        if e.key == "Space":
            answer_input.value = (answer_input.value or "") + " "
            page.update()
            return

        if len(e.key) == 1 and not any([getattr(e, "ctrl", False), getattr(e, "alt", False), getattr(e, "meta", False)]):
            key_text = e.key
            if key_text.isalpha() and not getattr(e, "shift", False):
                key_text = key_text.lower()
            answer_input.value = (answer_input.value or "") + key_text
            page.update()

    # Attach page-level keyboard handler
    page.on_keyboard_event = handle_page_key_event

    def start():
        show_current_question()

    content = ft.Column(
        controls=[
            progress_text,
            timer_bar,
            ft.Row([timer_label, ft.Container(width=20), timer_status]),
            card,
            ft.Container(height=20),
            answer_input,
            ft.Row(
                controls=[submit_btn, skip_btn],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )
    content.cleanup = cleanup
    content.start = start
    return content
