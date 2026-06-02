import datetime
from wod.bot.formatters import SessionSummary, SessionLogRow, UserProfile, session_summary_to_pdf

def test_pdf():
    summary = SessionSummary(
        title="Test Workout",
        date=datetime.datetime.now(),
        rows=[
            SessionLogRow(
                order=1,
                exercise_name="Panca Piana",
                set_number=1,
                kg="60",
                reps="10",
                rest="120s",
                intensity="Buffer 1",
                skipped=False,
            ),
            SessionLogRow(
                order=1,
                exercise_name="Panca Piana",
                set_number=2,
                kg="0",
                reps="0",
                rest="-",
                intensity="-",
                skipped=True,
            )
        ],
        user_profile=UserProfile(name="Test User", height_cm=180, weight_kg=80)
    )
    try:
        pdf_bytes = session_summary_to_pdf(summary)
        print("Success! PDF generated, size:", len(pdf_bytes))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf()
