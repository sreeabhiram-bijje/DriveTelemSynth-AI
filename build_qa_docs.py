"""Script to generate a professional PDF and companion printable HTML for DriveTelemSynth AI."""

import os
import sys

# -------------------------------------------------------------
# Document Data: Sections, Questions, and Answers
# -------------------------------------------------------------

SECTIONS = [
    {
        "title": "SECTION 1: PROJECT OVERVIEW & ELEVATOR PITCH",
        "description": "Foundational questions about the purpose, problem statement, and high-level architecture.",
        "qa": [
            {
                "q": "Q1. What is DriveTelemSynth AI? Give a 60-second summary of your project.",
                "a": (
                    "Sir, DriveTelemSynth AI is a Multi-Vehicle Comparative Driving Simulation and Intelligent Insurance Analytics Platform "
                    "developed using Python, Flask, NumPy, and Pandas.\n\n"
                    "In the automotive and insurance sectors, driving telematics data (GPS speed, braking, "
                    "acceleration) is vital for Usage-Based Insurance (UBI) and fleet analytics. However, "
                    "real telematics data is strictly gated by data protection regulations (GDPR, CCPA) "
                    "and proprietary restrictions.\n\n"
                    "DriveTelemSynth AI solves this by simulating and comparing multiple vehicles (Slow, Medium, High speeds) "
                    "under identical road speed limits. It features an animated HTML5 Canvas simulation studio, a 100-point "
                    "heuristic risk scoring model, automated insurance eligibility and discount assessments, safety rankings, "
                    "tailored driver coaching recommendations, and instant CSV/JSON exports."
                )
            },
            {
                "q": "Q2. What is Driving Telematics, and what is Usage-Based Insurance (UBI)?",
                "a": (
                    "Telematics is the combination of telecommunications and vehicular informatics, measuring "
                    "parameters such as vehicle speed, acceleration, braking severity, trip duration, and time of day.\n\n"
                    "Usage-Based Insurance (UBI), also known as Pay-How-You-Drive (PHYD), prices insurance premiums "
                    "based on actual driving behavior rather than solely on static demographics (such as age or credit score). "
                    "Safer drivers who accelerate smoothly, obey speed limits, and avoid late-night driving receive discounted premiums."
                )
            },
            {
                "q": "Q3. What are the key features and capabilities of your application?",
                "a": (
                    "1. Configurable Scenarios: Generates Safe Urban, Normal Mixed, Aggressive Highway, and Custom Risk profiles.\n"
                    "2. Physical Consistency: Enforces strict mathematical relationships: Duration = Distance / Speed * 60, and Max Speed >= Average Speed.\n"
                    "3. Poisson Event Modeling: Discrete simulation of harsh braking and acceleration events.\n"
                    "4. Heuristic Risk Scoring: 100-point formula classifying trips into Low, Medium, and High risk tiers.\n"
                    "5. Interactive Analytics Studio: Live dashboard with summary KPIs, distribution charts, and a 25-row preview table.\n"
                    "6. Secure & Bounded Architecture: Thread-safe in-memory cache with FIFO eviction (capped at 32 datasets) and zero driver data written to disk."
                )
            }
        ]
    },
    {
        "title": "SECTION 2: DATA GENERATION, MATHEMATICS & STATISTICS",
        "description": "How synthetic data is generated, mathematical distributions used, and physical realism.",
        "qa": [
            {
                "q": "Q4. Why did you use NumPy's default_rng(seed) instead of np.random.seed()?",
                "a": (
                    "In modern NumPy (v1.17+), default_rng() instantiates an independent Generator backed by the "
                    "PCG64 bit generator. In contrast, np.random.seed() alters a legacy global state that is not thread-safe "
                    "and can cause cross-request collision in web applications like Flask.\n\n"
                    "Using default_rng(seed) guarantees thread safety, superior statistical entropy, and perfect "
                    "reproducibility across different operating systems."
                )
            },
            {
                "q": "Q5. Why is the Poisson distribution used for harsh acceleration and braking events?",
                "a": (
                    "Driving incidents like harsh braking or rapid acceleration are discrete, independent events occurring "
                    "over a continuous distance. The Poisson distribution is the standard mathematical model for counting "
                    "the occurrences of an event in a fixed interval given a known average rate lambda.\n\n"
                    "In our generator, lambda is dynamically parameterized by trip distance: "
                    "lambda = rate_per_10km * (distance_km / 10). "
                    "NumPy then samples rng.poisson(lambda), producing natural integer counts with realistic variance."
                )
            },
            {
                "q": "Q6. How does the system ensure physical consistency between trip variables?",
                "a": (
                    "Naive synthetic generation often samples speed, distance, and duration independently, producing "
                    "illogical trips (e.g. 50 km driven in 20 minutes at 30 km/h).\n\n"
                    "DriveTelemSynth AI enforces physical laws:\n"
                    "- Average Speed and Distance are sampled first from scenario boundaries.\n"
                    "- Duration (in minutes) is computed deterministically: (distance_km / average_speed_kmh) * 60.0.\n"
                    "- Maximum Speed is calculated by adding a positive offset (5 to 58 km/h) to average speed: "
                    "maximum_speed = average_speed + offset, ensuring Maximum Speed >= Average Speed always."
                )
            },
            {
                "q": "Q7. How are synthetic driver identities generated, and why pool them?",
                "a": (
                    "We use the Faker library (seeded with the same seed) to generate realistic alphanumeric driver codes "
                    "(e.g., 'DRV-16658760').\n\n"
                    "Rather than generating a new driver ID for every trip, we generate a bounded pool of drivers "
                    "(up to 80 drivers for large batches) and randomly assign trips to this pool. This mirrors real fleet "
                    "dynamics where an individual driver completes multiple trips over time."
                )
            }
        ]
    },
    {
        "title": "SECTION 3: RISK SCORING HEURISTIC & ANALYTICS",
        "description": "Details of the 100-point risk heuristic, weighting criteria, and Pandas aggregations.",
        "qa": [
            {
                "q": "Q8. Explain the exact mathematical formula used to calculate the Risk Score.",
                "a": (
                    "The Risk Score is a transparent heuristic ranging from 0 to 100 points, calculated as:\n\n"
                    "1. Speeding Points (max 45): speeding_ratio * 45.0\n"
                    "2. Harsh Braking Points (max 20): min(harsh_braking_count / max(distance_km / 10, 1), 1.0) * 20.0\n"
                    "3. Harsh Acceleration Points (max 20): min(harsh_acceleration_count / max(distance_km / 10, 1), 1.0) * 20.0\n"
                    "4. Night Driving Points (max 15): night_driving_ratio * 15.0\n\n"
                    "Total Points = clip(Speeding + Braking + Acceleration + Night, 0, 100).\n"
                    "Final Score = floor(Total Points + 0.5) to produce an integer score."
                )
            },
            {
                "q": "Q9. How are drivers categorized into risk labels, and what are the thresholds?",
                "a": (
                    "Using np.select(), each trip is classified based on its integer risk score:\n"
                    "- Low Risk: Score < 35 (safe driving, low event rates, minimal speeding)\n"
                    "- Medium Risk: 35 <= Score < 65 (typical mixed driving behavior)\n"
                    "- High Risk: 65 <= Score <= 100 (aggressive driving, excessive speeding, frequent harsh events)"
                )
            },
            {
                "q": "Q10. How does the analytics engine calculate summary metrics for the dashboard?",
                "a": (
                    "The module analytics/summaries.py uses Pandas vectorization:\n"
                    "- KPIs: Total trips len(frame), unique drivers frame['driver_id'].nunique(), mean risk score, "
                    "high-risk percentage (frame['risk_label'] == 'High').mean() * 100, and mean speed.\n"
                    "- Risk Distribution: frame['risk_label'].value_counts().reindex(['Low', 'Medium', 'High']).\n"
                    "- Average Speed by Risk: frame.groupby('risk_label')['average_speed_kmh'].mean().\n"
                    "- Driving Events: Mean harsh acceleration and braking counts across all records."
                )
            }
        ]
    },
    {
        "title": "SECTION 4: BACKEND ARCHITECTURE & FLASK IMPLEMENTATION",
        "description": "Flask endpoints, request lifecycle, thread safety, and memory management.",
        "qa": [
            {
                "q": "Q11. Walk through the request-response lifecycle of POST /api/generate.",
                "a": (
                    "1. Request Reception: The client sends a JSON payload with records, scenario, seed, and optional custom_settings.\n"
                    "2. Payload Validation: validate_request() verifies JSON types, numeric bounds, and scenario names.\n"
                    "3. Data Generation: generate_dataset() samples NumPy distributions and calculates risk scores.\n"
                    "4. Memory Caching: A 24-character cryptographically secure token is generated (secrets.token_urlsafe). "
                    "The DataFrame is cached in DATASETS under a threading.Lock().\n"
                    "5. Response Serialization: build_summary() generates KPIs and charts JSON, and the first 25 rows "
                    "are returned with the temporary download URL."
                )
            },
            {
                "q": "Q12. How does the application prevent memory exhaustion with large datasets?",
                "a": (
                    "The application employs a bounded FIFO cache using Python's collections.OrderedDict:\n"
                    "- MAX_STORED_DATASETS is strictly capped at 32.\n"
                    "- Whenever a new dataset is generated, DATASETS.move_to_end(download_id) marks it as newest.\n"
                    "- A while loop checks: while len(DATASETS) > MAX_STORED_DATASETS: DATASETS.popitem(last=False).\n"
                    "- This automatically evicts the oldest dataset from RAM, preventing memory leaks on long server uptimes."
                )
            },
            {
                "q": "Q13. How does the CSV download work without creating physical files on disk?",
                "a": (
                    "When GET /download/<download_id> is requested, the DataFrame is retrieved from the in-memory cache. "
                    "It is serialized directly into memory using io.BytesIO(frame.to_csv(index=False).encode('utf-8')).\n\n"
                    "Flask's send_file() streams the byte stream directly to the HTTP response with mimetype='text/csv' "
                    "and Content-Disposition='attachment'. This ensures zero sensitive data is persisted to disk."
                )
            },
            {
                "q": "Q14. Why did you use threading.Lock() in DATASETS_LOCK?",
                "a": (
                    "Flask handles concurrent requests using multiple worker threads. Standard Python dictionaries "
                    "are not safe against simultaneous write/pop operations across threads. Without synchronization, "
                    "concurrent accesses could cause race conditions or KeyError exceptions. "
                    "threading.Lock() guarantees mutually exclusive, atomic cache operations."
                )
            }
        ]
    },
    {
        "title": "SECTION 5: INPUT VALIDATION, SECURITY & QUALITY ASSURANCE",
        "description": "Security measures, error handling, edge cases, and automated testing.",
        "qa": [
            {
                "q": "Q15. What security safeguards are built into the API?",
                "a": (
                    "1. Payload Size Limit: app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 (16 KB) prevents oversized payload DOS attacks.\n"
                    "2. Finite Value Checks: Uses math.isfinite() to block NaN or Infinity values.\n"
                    "3. Boolean Trap Prevention: In Python, bool is a subclass of int. Validation explicitly checks "
                    "if isinstance(val, bool) to block booleans from passing as integer counts.\n"
                    "4. Strict Range Clamping: Record count is capped between 1 and 10,000; random seed is limited to 32-bit unsigned int.\n"
                    "5. Secure Tokens: Secrets are generated with secrets.token_urlsafe(24) rather than predictable timestamps."
                )
            },
            {
                "q": "Q16. Explain your Pytest testing strategy and test results.",
                "a": (
                    "We have a full test suite in tests/test_app.py comprising 20 passing unit and integration tests:\n"
                    "- Parameterized Scenario Tests: Verifies all 4 scenarios generate valid non-null records matching physical constraints.\n"
                    "- Determinism Test: Confirms two runs with the same seed produce bit-for-bit identical DataFrames.\n"
                    "- Scenario Separation Test: Asserts Safe Urban has strictly lower speed, speeding ratio, and events than Aggressive Highway.\n"
                    "- Boundary & Validation Tests: Tests out-of-range records (0, 10,001), negative seeds, inverted speed ranges, and invalid JSON.\n"
                    "- API & Cache Lifecycle Tests: Exercises /health, /api/generate, valid CSV downloads, and 404 responses on expired tokens."
                )
            }
        ]
    },
    {
        "title": "SECTION 6: FRONTEND & DATA VISUALIZATION",
        "description": "User interface, asynchronous communication, Chart.js graphs, and UX design.",
        "qa": [
            {
                "q": "Q17. How does the frontend client interact with the backend?",
                "a": (
                    "The client-side JavaScript (static/js/main.js) uses modern asynchronous Fetch API.\n"
                    "When the user submits the form:\n"
                    "- It intercepts the event with e.preventDefault().\n"
                    "- Validates input fields and shows a spinner / loading state.\n"
                    "- Sends an HTTP POST to /api/generate-multiple with JSON payload.\n"
                    "- On success, updates the fleet KPI cards, Chart.js instances, comparison table, insurance cards, and preview table.\n"
                    "- On failure, displays human-readable error messages returned by the API."
                )
            },
            {
                "q": "Q18. What charts are rendered, and what business insights do they convey?",
                "a": (
                    "We use Chart.js v4 to render six analytical views:\n"
                    "1. Average Speed by Vehicle: Displays vehicle velocities against the posted road speed limit.\n"
                    "2. Risk Score Comparison: Compares overall heuristic scores across all fleet vehicles.\n"
                    "3. Simulated Insurance Premium: Visualizes final premiums incorporating safe-driving discounts.\n"
                    "4. Harsh Driving Events: Side-by-side comparison of harsh accelerations vs. harsh braking per trip.\n"
                    "5. Fleet Risk Tier Distribution: Doughnut breakdown of Low, Medium, and High risk vehicles.\n"
                    "6. Driving Behaviour Radar: Multi-axis profile comparing Speed, Braking, Acceleration, Night, and Speeding."
                )
            }
        ]
    },
    {
        "title": "SECTION 7: MULTI-VEHICLE SIMULATION & INSURANCE ELIGIBILITY",
        "description": "HTML5 Canvas road animation, relative speed modeling, and Pay-How-You-Drive underwriting.",
        "qa": [
            {
                "q": "Q19. How does the HTML5 Canvas Multi-Vehicle Driving Simulation work?",
                "a": (
                    "The simulation studio renders an animated multi-lane highway using the HTML5 Canvas 2D API.\n"
                    "Key mechanics:\n"
                    "- Lanes: Dynamically calculates lane heights for 2 to 5 concurrent vehicles.\n"
                    "- Relative Velocities: Each vehicle moves at a speed directly proportional to its configured speed.\n"
                    "- Animation Loop: requestAnimationFrame ensures 60 FPS smooth rendering with high-precision delta-time.\n"
                    "- Visual Realism: Features headlights with forward glow, taillights, wheel treads, vehicle labels, and live speed badges.\n"
                    "- Interactive Controls: Full playback control including Start, Pause, Resume, Reset, and live speed adjustment sliders."
                )
            },
            {
                "q": "Q20. Why does speed risk depend on relative road speed limits rather than absolute speed?",
                "a": (
                    "In real-world telematics underwriting, traveling at 100 km/h on a 120 km/h expressway is safe and legal, "
                    "whereas traveling at 60 km/h in a 30 km/h school zone is reckless. Our engine calculates the speeding ratio "
                    "relative to the configured road_speed_limit, ensuring vehicles driving at legal highway speeds are not unfairly penalized."
                )
            },
            {
                "q": "Q21. How does the Insurance Eligibility Engine calculate simulated premiums and discounts?",
                "a": (
                    "The engine (analytics/insurance.py) applies actuarial heuristic discount tiers based on risk scores:\n"
                    "- Low Risk (Score < 35): Preferred Safe Driver, awarded the maximum 20% discount (e.g. Rs. 8,000 on a Rs. 10,000 base).\n"
                    "- Medium Risk (Score 35-64): Standard Coverage, awarded a 5% baseline discount (Rs. 9,500).\n"
                    "- High Risk (Score >= 65): High Risk / Surcharge Tier, 0% discount (Rs. 10,000), flagged for underwriting review.\n"
                    "Each assessment includes a detailed plain-language explanation of the decision."
                )
            }
        ]
    }
]

# -------------------------------------------------------------
# Pure Python PDF Generator
# -------------------------------------------------------------

class PDFDocument:
    def __init__(self):
        self.pages = []
        self.current_page = []
        self.page_width = 595.28   # A4 width in pt
        self.page_height = 841.89  # A4 height in pt
        self.margin_x = 44.0
        self.margin_top = 48.0
        self.margin_bottom = 44.0
        self.usable_width = self.page_width - 2 * self.margin_x
        self.y = self.page_height - self.margin_top

    def new_page(self):
        if self.current_page:
            self.pages.append("".join(self.current_page))
            self.current_page = []
        self.y = self.page_height - self.margin_top

    def emit(self, s):
        self.current_page.append(s)

    def escape_pdf(self, text):
        replacements = {
            "\u2014": " -- ",
            "\u2013": "-",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2022": "*",
            "\u03bb": "lambda",
            "\u2265": ">=",
            "\u2264": "<=",
            "\u00b7": "*",
            "\u2192": "->",
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        text = text.encode("ascii", "replace").decode("ascii")
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def draw_text(self, text, x, y, font="F1", size=10, color=(0.1, 0.1, 0.1)):
        r, g, b = color
        safe = self.escape_pdf(text)
        self.emit(f"BT /{font} {size} Tf {r:.2f} {g:.2f} {b:.2f} rg {x:.2f} {y:.2f} Td ({safe}) Tj ET\n")

    def draw_rect(self, x, y, w, h, fill_color=None, stroke_color=None, line_width=1):
        self.emit(f"{line_width:.2f} w\n")
        if fill_color:
            r, g, b = fill_color
            self.emit(f"{r:.2f} {g:.2f} {b:.2f} rg\n")
        if stroke_color:
            r, g, b = stroke_color
            self.emit(f"{r:.2f} {g:.2f} {b:.2f} RG\n")
        op = "B" if (fill_color and stroke_color) else ("f" if fill_color else "S")
        self.emit(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re {op}\n")

    def draw_line(self, x1, y1, x2, y2, color=(0.7, 0.7, 0.7), width=0.5):
        r, g, b = color
        self.emit(f"{width:.2f} w {r:.2f} {g:.2f} {b:.2f} RG {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S\n")

    def wrap_text(self, text, max_chars):
        lines = []
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                lines.append("")
                continue
            words = paragraph.split(" ")
            current_line = []
            current_len = 0
            for word in words:
                word_len = len(word)
                if current_len + word_len + (1 if current_line else 0) <= max_chars:
                    current_line.append(word)
                    current_len += word_len + (1 if len(current_line) > 1 else 0)
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]
                    current_len = word_len
            if current_line:
                lines.append(" ".join(current_line))
        return lines

    def check_page_space(self, needed_pt):
        if self.y - needed_pt < self.margin_bottom:
            self.new_page()

    def add_header(self, page_num, total_pages):
        # Header line
        self.draw_text("DriveTelemSynth AI — Project Viva & Technical Q&A Guide", self.margin_x, self.page_height - 30, font="F2", size=8.5, color=(0.3, 0.35, 0.45))
        self.draw_line(self.margin_x, self.page_height - 34, self.page_width - self.margin_x, self.page_height - 34, color=(0.82, 0.85, 0.90), width=0.75)
        # Footer line
        self.draw_line(self.margin_x, 34, self.page_width - self.margin_x, 34, color=(0.82, 0.85, 0.90), width=0.75)
        self.draw_text("DriveTelemSynth AI · Educational & Viva Preparation Guide", self.margin_x, 22, font="F1", size=8, color=(0.45, 0.5, 0.55))
        page_str = f"Page {page_num} of {total_pages}"
        self.draw_text(page_str, self.page_width - self.margin_x - 55, 22, font="F2", size=8, color=(0.3, 0.35, 0.45))

    def save(self, filepath):
        if self.current_page:
            self.pages.append("".join(self.current_page))

        total_pages = len(self.pages)
        # Second pass: inject header and footer into each page stream
        final_pages = []
        for i, page_stream in enumerate(self.pages):
            self.current_page = []
            self.add_header(i + 1, total_pages)
            final_pages.append("".join(self.current_page) + page_stream)

        objects = []
        objects.append("<< /Type /Catalog /Pages 2 0 R >>") # 1
        objects.append("") # 2 placeholder for Pages
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>") # 3
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>") # 4
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>") # 5
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>") # 6

        current_obj = 7
        page_obj_ids = []
        content_obj_ids = []

        for _ in range(total_pages):
            page_obj_ids.append(current_obj)
            content_obj_ids.append(current_obj + 1)
            current_obj += 2

        kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
        objects[1] = f"<< /Type /Pages /Kids [{kids_str}] /Count {total_pages} >>"

        for i, page_stream in enumerate(final_pages):
            c_id = content_obj_ids[i]
            p_obj = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.page_width:.2f} {self.page_height:.2f}] "
                f"/Contents {c_id} 0 R /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R /F4 6 0 R >> >> >>"
            )
            stream_bytes = page_stream.encode("latin1")
            c_obj = f"<< /Length {len(stream_bytes)} >>\nstream\n{page_stream}\nendstream"
            objects.append(p_obj)
            objects.append(c_obj)

        with open(filepath, "wb") as f:
            f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            xref = [0]
            offset = f.tell()
            for idx, obj in enumerate(objects):
                xref.append(offset)
                obj_str = f"{idx + 1} 0 obj\n{obj}\nendobj\n"
                f.write(obj_str.encode("latin1"))
                offset = f.tell()

            xref_offset = offset
            f.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin1"))
            for off in xref[1:]:
                f.write(f"{off:010d} 00000 n \n".encode("latin1"))
            f.write(
                f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1")
            )


def build_pdf_document(filepath):
    pdf = PDFDocument()
    pdf.new_page()

    # --- Title Banner Block ---
    pdf.draw_rect(pdf.margin_x, pdf.y - 75, pdf.usable_width, 75, fill_color=(0.06, 0.16, 0.36), stroke_color=(0.1, 0.25, 0.5), line_width=1)
    pdf.draw_text("DRIVETELEMSYNTH AI", pdf.margin_x + 18, pdf.y - 25, font="F2", size=18, color=(1.0, 1.0, 1.0))
    pdf.draw_text("Project Viva, Oral Defense & Technical Master Q&A Guide", pdf.margin_x + 18, pdf.y - 42, font="F1", size=11, color=(0.85, 0.90, 0.98))
    pdf.draw_text("Tech Stack: Python 3 · Flask · NumPy · Pandas · Faker · Chart.js · Pytest", pdf.margin_x + 18, pdf.y - 60, font="F2", size=8.5, color=(0.4, 0.75, 1.0))
    pdf.y -= 90

    # --- Quick Metadata Table ---
    pdf.draw_rect(pdf.margin_x, pdf.y - 38, pdf.usable_width, 38, fill_color=(0.95, 0.97, 1.0), stroke_color=(0.8, 0.87, 0.95), line_width=0.75)
    pdf.draw_text("PROJECT DOMAIN: Automotive Telematics & Usage-Based Insurance (UBI)", pdf.margin_x + 10, pdf.y - 14, font="F2", size=8, color=(0.15, 0.25, 0.45))
    pdf.draw_text("KEY FEATURES: 4 Scenarios · 100-pt Risk Heuristic · Bounded In-Memory Cache · 100% Pytest Coverage", pdf.margin_x + 10, pdf.y - 28, font="F1", size=8, color=(0.25, 0.35, 0.5))
    pdf.y -= 50

    # Loop through sections and Q&As
    for section in SECTIONS:
        # Check space for section header (needs ~55 pt)
        pdf.check_page_space(55)

        # Section Header Banner
        pdf.draw_rect(pdf.margin_x, pdf.y - 24, pdf.usable_width, 24, fill_color=(0.12, 0.24, 0.48), stroke_color=None)
        pdf.draw_text(section["title"], pdf.margin_x + 10, pdf.y - 16, font="F2", size=10, color=(1.0, 1.0, 1.0))
        pdf.y -= 30

        # Section Subtitle / Description
        desc_lines = pdf.wrap_text(section["description"], max_chars=95)
        for dline in desc_lines:
            pdf.draw_text(dline, pdf.margin_x + 2, pdf.y - 8, font="F3", size=8.5, color=(0.35, 0.4, 0.45))
            pdf.y -= 12
        pdf.y -= 6

        # Q&As in this section
        for qa in section["qa"]:
            q_lines = pdf.wrap_text(qa["q"], max_chars=88)
            a_lines = pdf.wrap_text(qa["a"], max_chars=92)

            q_box_height = len(q_lines) * 13 + 10
            total_needed = q_box_height + len(a_lines) * 11 + 20

            # If not enough room for at least question and first 3 lines of answer, move to new page
            if pdf.y - (q_box_height + 40) < pdf.margin_bottom:
                pdf.new_page()

            # Draw Question Box
            pdf.draw_rect(pdf.margin_x, pdf.y - q_box_height, pdf.usable_width, q_box_height, fill_color=(0.94, 0.96, 0.99), stroke_color=(0.78, 0.84, 0.94), line_width=0.75)
            # Left accent stripe
            pdf.draw_rect(pdf.margin_x, pdf.y - q_box_height, 3.5, q_box_height, fill_color=(0.1, 0.45, 0.85))

            qy = pdf.y - 12
            for ql in q_lines:
                pdf.draw_text(ql, pdf.margin_x + 12, qy, font="F2", size=9.5, color=(0.08, 0.18, 0.38))
                qy -= 13
            pdf.y -= (q_box_height + 8)

            # Draw Answer Lines
            for al in a_lines:
                if pdf.y - 11 < pdf.margin_bottom:
                    pdf.new_page()
                if al.strip() == "":
                    pdf.y -= 6
                    continue
                # Highlight bullet points or sub-headers
                if al.strip().startswith(("-", "1.", "2.", "3.", "4.", "5.", "6.")):
                    pdf.draw_text(al, pdf.margin_x + 12, pdf.y - 8, font="F2" if any(al.strip().startswith(f"{i}.") for i in range(1, 7)) else "F1", size=8.5, color=(0.15, 0.2, 0.25))
                else:
                    pdf.draw_text(al, pdf.margin_x + 6, pdf.y - 8, font="F1", size=8.5, color=(0.18, 0.2, 0.25))
                pdf.y -= 11.5

            pdf.y -= 10  # Spacing between QA items

    pdf.save(filepath)
    print(f"PDF successfully saved to: {filepath} ({len(pdf.pages)} pages)")


# -------------------------------------------------------------
# Companion Printable HTML Generator
# -------------------------------------------------------------

def build_html_document(filepath):
    html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DriveTelemSynth AI — Project Viva & Oral Defense Q&A Guide</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #0f2744;
      --primary-light: #1e3a8a;
      --accent: #0284c7;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --text-main: #1e293b;
      --text-muted: #64748b;
      --code-bg: #f1f5f9;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      line-height: 1.6;
      padding: 40px 20px;
    }
    .container {
      max-width: 900px;
      margin: 0 auto;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 48px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.04);
    }
    .header-banner {
      background: linear-gradient(135deg, #09172c 0%, #17325b 100%);
      color: white;
      border-radius: 10px;
      padding: 32px;
      margin-bottom: 32px;
    }
    .header-banner h1 {
      font-size: 26px;
      font-weight: 700;
      letter-spacing: -0.5px;
      margin-bottom: 8px;
    }
    .header-banner p {
      color: #94a3b8;
      font-size: 14px;
      margin-bottom: 16px;
    }
    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .pill {
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.2);
      color: #38bdf8;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 20px;
    }
    .print-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #e0f2fe;
      border: 1px solid #bae6fd;
      padding: 12px 20px;
      border-radius: 8px;
      margin-bottom: 32px;
      font-size: 14px;
      color: #0369a1;
    }
    .btn-print {
      background: #0284c7;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      font-family: inherit;
    }
    .btn-print:hover { background: #0369a1; }
    .section-block {
      margin-bottom: 40px;
    }
    .section-title {
      font-size: 18px;
      font-weight: 700;
      color: var(--primary);
      border-bottom: 2px solid var(--accent);
      padding-bottom: 8px;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .section-desc {
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 20px;
      font-style: italic;
    }
    .qa-card {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 8px;
      margin-bottom: 20px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .q-header {
      background: #f8fafc;
      border-left: 4px solid var(--accent);
      padding: 14px 18px;
      font-weight: 700;
      font-size: 15px;
      color: var(--primary);
      border-bottom: 1px solid var(--border);
    }
    .a-body {
      padding: 18px;
      font-size: 14px;
      color: #334155;
      white-space: pre-line;
      line-height: 1.65;
    }
    .a-body code {
      font-family: 'JetBrains Mono', monospace;
      background: var(--code-bg);
      padding: 2px 5px;
      border-radius: 4px;
      font-size: 12.5px;
      color: #0369a1;
    }
    @media print {
      body { background: white; padding: 0; }
      .container { border: none; box-shadow: none; padding: 0; max-width: 100%; }
      .print-bar { display: none; }
      .qa-card { page-break-inside: avoid; }
      .header-banner { background: #0f2744 !important; color: white !important; -webkit-print-color-adjust: exact; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="print-bar">
      <span>💡 <strong>Tip for Viva:</strong> You can print this directly or press <strong>Ctrl + P</strong> to save as a PDF.</span>
      <button class="btn-print" onclick="window.print()">🖨️ Print / Save as PDF</button>
    </div>

    <div class="header-banner">
      <h1>DRIVETELEMSYNTH AI</h1>
      <p>Comprehensive Viva, Oral Defense & Technical Master Q&A Guide</p>
      <div class="pill-row">
        <span class="pill">Python 3</span>
        <span class="pill">Flask</span>
        <span class="pill">NumPy</span>
        <span class="pill">Pandas</span>
        <span class="pill">Faker</span>
        <span class="pill">Chart.js</span>
        <span class="pill">Pytest (20/20 Passed)</span>
      </div>
    </div>
"""

    for section in SECTIONS:
        html += f"""
    <div class="section-block">
      <h2 class="section-title">{section['title']}</h2>
      <p class="section-desc">{section['description']}</p>
"""
        for qa in section["qa"]:
            html += f"""
      <div class="qa-card">
        <div class="q-header">{qa['q']}</div>
        <div class="a-body">{qa['a']}</div>
      </div>
"""
        html += "    </div>\n"

    html += """
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border); font-size: 12px; color: var(--text-muted); text-align: center;">
      DriveTelemSynth AI · Synthetic Driving Telematics Studio · Prepared for Academic Defense & Viva
    </footer>
  </div>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML successfully saved to: {filepath}")


if __name__ == "__main__":
    pdf_out = os.path.abspath("DriveTelemSynth_AI_Viva_QA_Guide.pdf")
    html_out = os.path.abspath("DriveTelemSynth_AI_Viva_QA_Guide.html")
    build_pdf_document(pdf_out)
    build_html_document(html_out)
