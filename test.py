from flask import Flask, request, jsonify, render_template_string, session as flask_session, redirect
from datetime import timedelta
import os
import requests

app = Flask(__name__)

# Required so Flask can store each browser user's backend cookie jar in a signed browser cookie.
# For real deployment, set FLASK_SECRET_KEY in your environment.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-change-this-secret-key")
app.permanent_session_lifetime = timedelta(days=7)

# Your Node/Express backend. Keep 127.0.0.1 if Flask and Node run on the same VPS.
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:4000")


# =============================================================================
# Program planning sheet data, manually encoded from the uploaded BU ENG PPS PDFs.
# =============================================================================

TERM_LABELS = [
    "Completed / Transferred",
    "Freshman Fall",
    "Freshman Spring",
    "Freshman Summer",
    "Sophomore Fall",
    "Sophomore Spring",
    "Sophomore Summer",
    "Junior Fall",
    "Junior Spring",
    "Junior Summer",
    "Senior Fall",
    "Senior Spring",
    "Senior Summer",
    "Extra Semester",
]

MAJOR_DATA = {
    "Electrical Engineering": {
        "abbr": "EE",
        "units": 131,
        "required_plan": {
            "Freshman Fall": [
                ["CAS MA 123", "Calculus I"],
                ["Natural Science Elective", "Choose from approved EE natural science list"],
                ["ENG EK 100", "Freshman Seminar"],
                ["ENG EK 125", "Programming for Engineers"],
                ["CAS WR 120", "Writing Seminar"],
            ],
            "Freshman Spring": [
                ["CAS MA 124", "Calculus II"],
                ["CAS PY 211", "Physics I"],
                ["ENG EK 131", "Introduction to Engineering"],
                ["ENG EK 103", "Computational Linear Algebra"],
                ["CAS WR 15x", "Writing, Research & Inquiry"],
            ],
            "Sophomore Fall": [
                ["CAS MA 225", "Multivariable Calculus"],
                ["CAS PY 212", "Physics II"],
                ["ENG EK 307", "Electric Circuits"],
                ["ENG EK 210", "Introduction to Engineering Design"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Sophomore Spring": [
                ["CAS MA 226", "Differential Equations"],
                ["CAS PY 313", "Modern Physics"],
                ["ENG EK 301", "Engineering Mechanics"],
                ["ENG EK 381", "Probability, Statistics & Data Science"],
            ],
            "Junior Fall": [
                ["ENG EC 455", "Electromagnetic Systems I"],
                ["ENG EC 401", "Signals & Systems"],
                ["ENG EC 410", "Introduction to Electronics"],
                ["ENG EC 311", "Introduction to Logic Design"],
            ],
            "Junior Spring": [
                ["EE Core Elective", "Choose EE core elective"],
                ["EE Core Elective", "Choose EE core elective"],
                ["EE Core Elective", "Choose EE core elective"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Senior Fall": [
                ["Computer Elective", "Choose approved computer elective"],
                ["Technical Elective", "Choose approved technical elective"],
                ["ENG EC 463", "Senior Design I"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Senior Spring": [
                ["Technical Elective", "Choose approved technical elective"],
                ["Technical Elective", "Choose approved technical elective"],
                ["ENG EC 464", "Senior Design II"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
        },
        "dropdowns": {
            "Natural Science Elective": [
                "CAS AS 202 - Principles of Astronomy 1",
                "CAS BI 107 - Biology 1",
                "CAS BI 108 - Biology 2",
                "CAS CH 101 - General Chemistry 1",
                "CAS CH 131 - Gen Chem for the Eng Sci",
                "CAS PY 451 - Quantum Physics 1",
            ],
            "EE Core Elective": [
                "ENG EC 402 - Control System",
                "ENG EC 414 - Machine Learning",
                "ENG EC 415 - Software Radios",
                "ENG EC 418 - Intro to Reinforcement Learning",
                "ENG EC 501 - Dynamic System Theory",
                "ENG EC 503 - Intro to Learning from Data",
                "ENG EC 505 - Stochastic Processes",
                "ENG EC 508 - Wireless Communication",
                "ENG EC 515 - Digital Communication",
                "ENG EC 516 - Digital Signals Processing",
                "ENG EC 517 - Intro to Information Theory",
                "ENG EC 519 - Speech Processing by Humans & Machn",
                "ENG EC 520 - Digital Image Processing & Comm",
                "ENG EC 522 - Computational Optical Imaging",
                "ENG EC 523 - Deep Learning",
                "ENG EC 524 - Optimization Theory & Methods",
                "ENG EC 525 - Optimization for Machine Learning",
                "ENG EC 534 - Discrete Stochastic Models",
                "ENG EC 541 - Computer Communication Networks",
                "ENG EC 412 - Analog Electronics",
                "ENG EC 417 - Electric Energy Systems",
                "ENG EC 571 - Digital VLSI Circuit Design",
                "ENG EC 580 - Analog VLSI Circuit Design",
                "ENG EC 582 - RF/Analog IC Design",
                "ENG EC 583 - Power Electronics for Energy Systems",
                "ENG EC 456 - Electromagnetic Systems II",
                "ENG EC 471 - Physics of Semiconductor Devices",
                "ENG EC 543 - Sustainable Power Systems",
                "ENG EC 555 - Intro to Bio Optics",
                "ENG EC 556 - Optical Spectroscopic Imaging",
                "ENG EC 560 - Intro to Photonics",
                "ENG EC 562 - Engineering Optics",
                "ENG EC 565 - Electromagnetic Energy Trans",
                "ENG EC 568 - Optical Fibers & Wave Guides",
                "ENG EC 570 - Lasers & Applications",
                "ENG EC 572 - Computational Methods in Mtls Sci",
                "ENG EC 573 - Solar Energy Systems",
                "ENG EC 574 - Physics of Semiconductor Materials",
                "ENG EC 575 - Semiconductor Devices",
                "ENG EC 577 - Electronic Optical & Magnetic Prop Mtls",
                "ENG EC 578 - Fabrication Tech for Integrated Circuits",
                "ENG EC 579 - Nano/microelectronic Device Technology",
                "ENG EC 585 - Quantum ENG & Tech",
                "ENG EC 591 - Photonics Laboratory I",
                "ENG EK 481 - Intro to Nanotechnology",
            ],
            "Computer Elective": [
                "ENG EC 327 - Intro Software Engineering",
                "ENG EC 413 - Computer Organization",
                "ENG EC 441 - Introduction to Computer Networking",
            ],
            "Technical Elective": [
                "ENG BE 209 - Principles of Molecular Cell Biology and Biotechnology",
                "CAS AS 414 - Solar and Space Physics",
                "CAS CS 440 - Intro to Artificial Intelligence",
                "CAS CS 480 - Introduction to Computer Graphics",
                "CAS CS 585 - Image and Video Computing",
                "CAS MA 511 - Introduction to Analysis",
                "CAS MA 528 - Introduction to Modern Geometry",
                "CAS MA 531 - Computability and Logic",
                "CAS MA 541 - Modern Algebra 1",
                "CAS MA 583 - Introduction to Stochastic Processes",
                "CAS PY 451 - Quantum Physics 1",
                "CAS PY 452 - Quantum Physics 2",
                "Other approved ENG EC/BE/EK/ME 300+ course",
            ],
            "Hub Elective": ["Use Course Search to choose a Hub course"],
        },
    },

    "Computer Engineering": {
        "abbr": "CE",
        "units": 133,
        "required_plan": {
            "Freshman Fall": [
                ["CAS MA 123", "Calculus I"],
                ["Natural Science Elective", "Choose from approved CE natural science list"],
                ["ENG EK 100", "Freshman Seminar"],
                ["ENG EK 125", "Programming for Engineers"],
                ["CAS WR 120", "Writing Seminar"],
            ],
            "Freshman Spring": [
                ["CAS MA 124", "Calculus II"],
                ["CAS PY 211", "Physics I"],
                ["ENG EK 131", "Introduction to Engineering"],
                ["ENG EK 103", "Computational Linear Algebra"],
                ["CAS WR 15x", "Writing, Research & Inquiry"],
            ],
            "Sophomore Fall": [
                ["CAS MA 225", "Multivariable Calculus"],
                ["CAS PY 212", "Physics II"],
                ["ENG EK 307", "Electric Circuits"],
                ["ENG EC 327", "Introduction to Software Engineering"],
                ["CAS MA 193", "Intro Discrete Math"],
            ],
            "Sophomore Spring": [
                ["CAS MA 226", "Differential Equations"],
                ["ENG EC 311", "Introduction to Logic Design"],
                ["ENG EK 301", "Engineering Mechanics"],
                ["ENG EK 210", "Introduction to Engineering Design"],
                ["ENG EC 330", "Applied Algebra for Engineering"],
            ],
            "Junior Fall": [
                ["ENG EK 381", "Probability, Statistics & Data Science"],
                ["ENG EC 413", "Computer Organization"],
                ["CE Core Elective", "Choose approved CE core elective"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Junior Spring": [
                ["EE Breadth Elective", "Choose approved EE breadth elective"],
                ["Computer Engineering Elective", "Choose approved CE elective"],
                ["CE Core Elective", "Choose approved CE core elective"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Senior Fall": [
                ["Computer Engineering Elective", "Choose approved CE elective"],
                ["Technical Elective", "Choose approved technical elective"],
                ["ENG EC 463", "Senior Design I"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Senior Spring": [
                ["Technical Elective", "Choose approved technical elective"],
                ["Technical Elective", "Choose approved technical elective"],
                ["ENG EC 464", "Senior Design II"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
        },
        "dropdowns": {
            "Natural Science Elective": [
                "CAS AS 202 - Principles of Astronomy 1",
                "CAS BI 107 - Biology 1",
                "CAS BI 108 - Biology 2",
                "CAS CH 101 - General Chemistry 1",
                "CAS CH 131 - Gen Chem for the Eng Sci",
                "CAS PY 313 - Waves and Modern Physics",
                "CAS PY 314 - Waves and Modern Physics (Grenoble)",
                "CAS PY 321 & 322 - Thermal Physics & Quantum Physics",
                "CAS PY 451 - Quantum Physics 1",
            ],
            "CE Core Elective": [
                "ENG EC 401 - Signals and Systems",
                "ENG EC 410 - Introduction to Electronics",
                "ENG EC 440 - Introduction to Operating Systems",
                "ENG EC 441 - Introduction to Computer Networking",
                "ENG EC 444 - Smart and Connected Systems",
            ],
            "Computer Engineering Elective": [
                "ENG EC 440 - Introduction to Operating Systems",
                "ENG EC 441 - Intro to Computer Networking",
                "ENG EC 444 - Smart & Connected Systems",
                "ENG EC 447 - Software Design",
                "ENG EC 504 - Advanced Data Structures",
                "ENG EC 512 - Enterprise Client-Server Software System Design",
                "ENG EC 513 - Computer Architecture",
                "ENG EC 518 - Robot Learning",
                "ENG EC 521 - Cybersecurity",
                "ENG EC 526 - Parallel Programming for High Performance & Big Data",
                "ENG EC 527 - High Performance Programming with Multicore & GPUs",
                "ENG EC 528 - Cloud Computing",
                "ENG EC 530 - Software Engineering Principles",
                "ENG EC 531 - Full-Stack Software at Scale",
                "ENG EC 535 - Introduction to Embedded Systems",
                "ENG EC 541 - Computer Communications Networks",
                "ENG EC 544 - Network Physical World",
                "ENG EC 545 - Cyber Physical Systems",
                "ENG EC 551 - Adv Digital Design w/ Verilog & FPGA",
                "ENG EC 552 - Computational Synthetic Biology",
                "ENG EC 571 - Digital VLSI Circuit Design",
                "CAS CS 320 - Concepts of Programming Languages",
                "CAS CS 350 - Fundamentals of Computing Systems",
                "CAS CS 410 - Advanced Software Systems",
                "CAS CS 411 - Software Engineering",
                "CAS CS 505 - Natural Language Processing",
                "CAS CS 511 - Formal Methods",
                "CAS CS 525 - Compiler Design",
                "CAS CS 530 - Advanced Algorithms",
                "CAS CS 535 - Complexity Theory",
                "CAS CS 538 - Fundamentals of Cryptography",
                "CAS CS 548 - Cryptography",
                "CAS CS 552 - Operating Systems",
                "CAS CS 558 - Computer Network Security",
                "CAS CS 562 - Database Applications",
                "CAS CS 565 - Data Mining",
            ],
            "EE Breadth Elective": [
                "ENG EC 401 - Signals and Systems",
                "ENG EC 410 - Introduction to Electronics",
                "ENG EC 455 - Electromagnetic Systems I",
                "Any EE core elective except EC 541 and EC 571",
            ],
            "Technical Elective": [
                "Any Computer Engineering Elective",
                "ENG BE 209 - Principles of Molecular Cell Biology and Biotechnology",
                "CAS AS 414 - Solar and Space Physics",
                "CAS CS 440 - Intro to Artificial Intelligence",
                "CAS CS 480 - Introduction to Computer Graphics",
                "CAS CS 585 - Image and Video Computing",
                "CAS MA 511 - Introduction to Analysis",
                "CAS MA 528 - Introduction to Modern Geometry",
                "CAS MA 531 - Computability and Logic",
                "CAS MA 541 - Modern Algebra 1",
                "CAS MA 583 - Introduction to Stochastic Processes",
                "CAS PY 313 - Waves and Modern Physics",
                "CAS PY 314 - Waves and Modern Physics",
                "CAS PY 451 - Quantum Physics 1",
                "CAS PY 452 - Quantum Physics 2",
                "Other approved ENG EC/BE/EK/ME 300+ course",
            ],
            "Hub Elective": ["Use Course Search to choose a Hub course"],
        },
    },

    "Mechanical Engineering": {
        "abbr": "ME",
        "units": 135,
        "required_plan": {
            "Freshman Fall": [
                ["CAS MA 123", "Calculus I"],
                ["CAS CH 131", "General Chemistry for Engineering"],
                ["ENG EK 100", "Freshman Seminar"],
                ["ENG EK 125", "Programming for Engineers"],
                ["CAS WR 120", "Writing Seminar"],
            ],
            "Freshman Spring": [
                ["CAS MA 124", "Calculus II"],
                ["CAS PY 211", "Physics I"],
                ["ENG EK 131", "Introduction to Engineering"],
                ["ENG EK 103", "Computational Linear Algebra"],
                ["CAS WR 15X", "Writing, Research & Inquiry"],
            ],
            "Sophomore Fall": [
                ["CAS MA 225", "Multivariable Calculus"],
                ["CAS PY 212", "Physics II"],
                ["ENG EK 307", "Electric Circuits"],
                ["ENG ME 357", "Intro to CAD"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Sophomore Spring": [
                ["CAS MA 226", "Differential Equations"],
                ["ENG EK 381", "Probability, Statistics & Data Science"],
                ["ENG EK 301", "Engineering Mechanics"],
                ["ENG EK 210", "Introduction to Engineering Design"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Junior Fall": [
                ["ENG ME 304", "Energy & Thermodynamics"],
                ["ENG ME 303", "Fluid Mechanics"],
                ["ENG ME 305", "Mechanics of Materials"],
                ["ENG ME 358", "Manufacturing Processes"],
                ["ENG ME 306", "Materials Science"],
            ],
            "Junior Spring": [
                ["Advanced Elective", "Choose approved advanced elective"],
                ["ENG ME 310", "Measurements & Instrumentation"],
                ["ENG ME 302", "Engineering Mechanics II"],
                ["ENG ME 360", "Electromechanical Design"],
            ],
            "Senior Fall": [
                ["Advanced Elective", "Choose approved advanced elective"],
                ["ENG ME 419", "Heat Transfer"],
                ["ENG ME 460", "Senior Design I"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Senior Spring": [
                ["Advanced Elective", "Choose approved advanced elective"],
                ["Advanced Elective", "Choose approved advanced elective"],
                ["ENG ME 461", "Senior Design II"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
        },
        "dropdowns": {
            "Advanced Elective": [
                "Any ENG 300+ course, if no significant overlap",
                "ENG ME 452 - Approved ME advanced elective",
                "ENG ME 457 - Approved ME advanced elective",
                "CAS AS 414 - Solar and Space Physics",
                "CAS PY 313 - Waves and Modern Physics",
                "CAS PY 314 - Waves and Modern Physics (Grenoble)",
                "CAS PY 321 & 322 - Thermal Physics & Quantum Physics",
                "ENG BE 209 - Molecular Cell Biology and Biotechnology",
                "HUB XC 433 - Art & Science of Technology Consulting",
                "HUB XC 438 - Art & Sci of Tech Consulting",
                "QST SI 480 - Business of Technology Innovation",
                "QST SI 482 - Technology and its Commercialization",
                "Other approved 300+ math/natural science by petition",
            ],
            "Hub Elective": ["Use Course Search to choose a Hub course"],
        },
    },

    "Biomedical Engineering": {
        "abbr": "BME",
        "units": 133,
        "required_plan": {
            "Freshman Fall": [
                ["CAS MA 123", "Calculus I"],
                ["ENG EK 100", "Freshman Seminar"],
                ["CAS CH 101", "Chemistry I"],
                ["ENG EK 125", "Programming for Engineers"],
                ["CAS WR 120", "Writing Seminar"],
            ],
            "Freshman Spring": [
                ["CAS MA 124", "Calculus II"],
                ["CAS PY 211", "Physics I"],
                ["CAS CH 102", "Chemistry II"],
                ["ENG EK 131", "Introduction to Engineering"],
                ["ENG EK 103", "Computational Linear Algebra"],
            ],
            "Sophomore Fall": [
                ["CAS MA 225", "Multivariable Calculus"],
                ["CAS PY 212", "Physics II"],
                ["ENG EK 307", "Electric Circuits"],
                ["ENG EK 210", "Introduction to Engineering Design"],
                ["CAS WR 15x", "Writing, Research & Inquiry"],
            ],
            "Sophomore Spring": [
                ["CAS MA 226", "Differential Equations"],
                ["ENG BE 209", "Principles of Molecular Cell Biology & Biotech"],
                ["ENG EK 301", "Engineering Mechanics"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Junior Fall": [
                ["ENG EK 381", "Probability, Statistics & Data Science"],
                ["CAS BI 315", "Systems Physiology"],
                ["ENG BE 403", "Signals & Controls"],
                ["ENG BE 493", "BME Measurements & Analysis"],
            ],
            "Junior Spring": [
                ["ENG BE 424", "Thermodynamics & Statistical Mechanics"],
                ["Fields Elective", "Choose Continua & Fields elective"],
                ["BME Design Elective", "Choose BME design elective"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Senior Fall": [
                ["ENG Elective", "Choose engineering elective"],
                ["Professional Elective", "Choose professional elective"],
                ["BME Elective", "Choose BME elective"],
                ["ENG BE 465", "Senior Design I"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
            "Senior Spring": [
                ["BME Elective", "Choose BME elective"],
                ["Professional Elective", "Choose professional elective"],
                ["ENG BE 466", "Senior Design II"],
                ["Hub Elective", "Choose remaining Hub area"],
            ],
        },
        "dropdowns": {
            "Fields Elective": [
                "ENG BE 420 - Introduction to Solid Biomechanics",
                "ENG BE 435 - Transport Phenomena in Living Systems",
                "ENG BE 436 - Fundamentals of Fluid Mechanics",
            ],
            "Professional Elective": [
                "Any suitable ENG BE/EC/EK/ME 300, 400, 500 level course",
                "CAS CH 203 - Organic Chemistry 1",
                "CAS CH 204 - Organic Chemistry 2",
                "CAS CH 300/400/500 level course except excluded courses",
                "CAS PY 300/400/500 level course except excluded courses",
                "CAS MA 300/400/500 level course except excluded courses",
                "CAS BI 206 - Genetics",
                "CAS BI 216 - Intensive Cell Biology",
                "CAS BI 300/400/500 level course except excluded courses",
                "ENG ME 357 - Intro to CAD",
                "ENG ME 358 - Design & Manufacture",
                "HUB XC 433 - Art & Science of Technology Consulting",
                "HUB XC 438 - Art & Sci of Tech Consulting",
                "QST SI 480 - Business of Technology Innovation",
                "QST SI 482 - Technology & Its Commercialization",
            ],
            "ENG Elective": [
                "ENG BE 404 - Advanced Controls",
                "ENG BE 420 - Intro to Solid Biomechanics",
                "ENG BE 425 - Intro to Biomedical Materials Science",
                "ENG BE 435 - Transport Phenomena in Living Tissues",
                "ENG BE 436 - Fundamentals Fluid Mechanics",
                "ENG BE 471 - Quantitative Neuroscience",
                "ENG BE 503 - Comp Methods in Biomed",
                "ENG BE 508 - Quant Studies Resp & Card Sys",
                "ENG BE 511 - Biomedical Instrumentation",
                "ENG BE 517 - Optical Microscopy of Biological Materials",
                "ENG BE 518 - Modern Optical Microscopy for Biomedical Imaging",
                "ENG BE 521 - Continuum Mechanics BME",
                "ENG BE 533 - Biorheology",
                "ENG BE 526 - Fundamentals of Biomaterials",
                "ENG BE 549 - Struct & Function Extracellular Matrix",
                "ENG BE 552 - Computational Synthetic Biology",
                "ENG BE 555 - Introduction to Biomedical Optics",
                "ENG BE 556 - Optical Spectroscopic Imaging",
                "ENG BE 557 - Programming Fundamentals for BME Data Analysis",
                "ENG BE 559 - Foundations Biomedical Data Science & ML",
                "ENG BE 562 - Computational Bio: ML Fundamentals",
                "ENG BE 567 - Nonlinear Systems in BME",
                "ENG BE 571 - Intro to Neuroengineering",
                "ENG BE 572 - Neurotechnology Devices",
                "ENG EC 311 - Intro to Logic Design",
                "ENG EC 327 - Intro Software Engineering",
                "ENG EC 410 - Intro to Electronics",
                "ENG EC 414 - Intro to Machine Learning",
                "ENG EC 455 - Electromagnetic Systems I",
                "ENG EC 471 - Physics Semiconductor Devices",
                "ENG EC 503 - Intro to Learning from Data",
                "ENG EC 505 - Stochastic Processes",
                "ENG EC 516 - Digital Signal Processing",
                "ENG EC 522 - Intro to Computational Imaging",
                "ENG EC 526 - Parallel Algorithms for High Performance Computing",
                "ENG EK 481 - Nanomaterials & Nanotechnology",
                "ENG ME 302 - Engineering Mechanics II",
                "ENG ME 305 - Mechanics of Materials",
                "ENG ME 309 - Structural Materials",
                "ENG ME 419 - Heat Transfer",
                "ENG ME 441 - Mechanical Vibrations",
                "ENG ME 503 - Kinetic Processes in Materials",
                "ENG ME 555 - MEMS: Fabrication & Materials",
                "ENG ME 571 - Medical Robotics",
            ],
            "BME Elective": [
                "Any ENG BE 400 or 500 level course except BE 451, BE 452, and BE 500",
                "BE 451/BE 500/600-level/700-level by petition only",
            ],
            "BME Design Elective": [
                "ENG BE 428 - Device Diagnostics & Design",
                "ENG BE 468 - Clinical Applications of Biomedical Design",
                "ENG BE 478 - Engineering Design for Refugee Health",
            ],
            "Hub Elective": ["Use Course Search to choose a Hub course"],
        },
    },
}


# Expand technical/elective searchable option lists so the UI can search the actual planning-sheet
# option pools for the selected major. These are still labels from the uploaded PPS sheets;
# broad categories remain when the sheet allows broad categories rather than naming every course.
def _unique_options(*lists):
    out = []
    seen = set()
    for lst in lists:
        for item in lst:
            key = item.strip().lower()
            if key and key not in seen:
                seen.add(key)
                out.append(item)
    return out

# EE technical electives may include all EC courses, ENG BE 209, many ENG BE/EK/ME 300+ courses,
# and the outside approved list. Include the named EC core/computer options so the searchable
# dropdown is useful instead of only showing the outside-course exceptions.
MAJOR_DATA["Electrical Engineering"]["dropdowns"]["Technical Elective"] = _unique_options(
    MAJOR_DATA["Electrical Engineering"]["dropdowns"].get("EE Core Elective", []),
    MAJOR_DATA["Electrical Engineering"]["dropdowns"].get("Computer Elective", []),
    MAJOR_DATA["Electrical Engineering"]["dropdowns"].get("Technical Elective", []),
)

# CE technical electives may include any CE elective, plus other approved engineering/outside courses.
MAJOR_DATA["Computer Engineering"]["dropdowns"]["Technical Elective"] = _unique_options(
    MAJOR_DATA["Computer Engineering"]["dropdowns"].get("Computer Engineering Elective", []),
    MAJOR_DATA["Computer Engineering"]["dropdowns"].get("CE Core Elective", []),
    MAJOR_DATA["Computer Engineering"]["dropdowns"].get("EE Breadth Elective", []),
    [x for x in MAJOR_DATA["Computer Engineering"]["dropdowns"].get("Technical Elective", []) if x != "Any Computer Engineering Elective"],
)

# ME calls this requirement Advanced Elective on the planning sheet. Add a Technical Elective
# alias so the UI behaves consistently when users search for technical-style electives.
MAJOR_DATA["Mechanical Engineering"]["dropdowns"]["Technical Elective"] = MAJOR_DATA["Mechanical Engineering"]["dropdowns"].get("Advanced Elective", [])

# BME does not label a slot as Technical Elective on the PPS, but the professional/elective
# pools are the practical searchable technical choices for BME.
MAJOR_DATA["Biomedical Engineering"]["dropdowns"]["Technical Elective"] = _unique_options(
    MAJOR_DATA["Biomedical Engineering"]["dropdowns"].get("Professional Elective", []),
    MAJOR_DATA["Biomedical Engineering"]["dropdowns"].get("ENG Elective", []),
    MAJOR_DATA["Biomedical Engineering"]["dropdowns"].get("BME Elective", []),
    MAJOR_DATA["Biomedical Engineering"]["dropdowns"].get("BME Design Elective", []),
    MAJOR_DATA["Biomedical Engineering"]["dropdowns"].get("Fields Elective", []),
)


def make_backend_session():
    """Create a requests session and load this browser user's saved backend cookies."""
    s = requests.Session()
    for name, value in flask_session.get("backend_cookies", {}).items():
        s.cookies.set(name, value)
    return s


def save_backend_cookies(s):
    """Save backend cookies back into the Flask browser session."""
    flask_session["backend_cookies"] = requests.utils.dict_from_cookiejar(s.cookies)
    flask_session.permanent = True
    flask_session.modified = True


def backend_request(method, path, json_body=None, params=None, timeout=25):
    s = make_backend_session()
    url = BACKEND_URL + path
    response = s.request(method, url, json=json_body, params=params, timeout=timeout)
    save_backend_cookies(s)
    return response


BASE_HTML = r"""
<!DOCTYPE html>
<html>
<head>
  <title>BU Course Scheduler</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      --bg: #f4f6fa;
      --panel: #ffffff;
      --ink: #111827;
      --muted: #6b7280;
      --blue: #2563eb;
      --blue-dark: #1d4ed8;
      --green: #059669;
      --red: #dc2626;
      --border: #d1d5db;
      --soft: #eef2ff;
      --purple: #ede9fe;
      --yellow: #fff7ed;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }

    header {
      background: #111827;
      color: white;
      padding: 16px 24px;
    }

    header h1 {
      margin: 0 0 8px 0;
      font-size: 24px;
    }

    nav {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }

    nav a, nav button {
      color: white;
      background: #374151;
      text-decoration: none;
      padding: 9px 12px;
      border-radius: 8px;
      border: none;
      cursor: pointer;
      font-size: 14px;
    }

    nav a:hover, nav button:hover {
      background: #4b5563;
    }

    main {
      padding: 10px;
      max-width: none;
      width: 100%;
      margin: 0;
      box-sizing: border-box;
    }

    section, .panel {
      background: var(--panel);
      border-radius: 12px;
      padding: 12px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.08);
      margin-bottom: 12px;
    }

    h2 { margin: 0 0 8px; font-size: 18px; }
    h3 { margin: 8px 0 6px; font-size: 14px; }

    input, textarea, button, select {
      width: 100%;
      padding: 7px 8px;
      margin: 4px 0;
      border-radius: 8px;
      border: 1px solid var(--border);
      font-size: 14px;
    }

    textarea { min-height: 54px; resize: vertical; }

    button {
      background: var(--blue);
      color: white;
      font-weight: bold;
      border: none;
      cursor: pointer;
    }

    button:hover { background: var(--blue-dark); }
    button.secondary { background: #4b5563; }
    button.success { background: var(--green); }
    button.danger { background: var(--red); }
    button.small { width: auto; padding: 6px 9px; font-size: 12px; margin: 3px; }

    .grid-2 {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 18px;
    }

    .grid-3 {
      display: grid;
      grid-template-columns: repeat(2, minmax(220px, 1fr));
      gap: 10px;
    }

    .builder-page {
      width: calc(100vw - 24px);
      max-width: none;
      margin-left: calc(50% - 50vw + 12px);
      margin-right: calc(50% - 50vw + 12px);
    }

    .builder-top {
      margin-bottom: 10px;
    }

    .builder-workspace {
      display: grid;
      grid-template-columns: minmax(0, 2.2fr) minmax(300px, 0.9fr);
      gap: 12px;
      align-items: start;
      width: 100%;
    }

    .schedule-side, .required-side {
      min-width: 0;
    }

    .settings-grid {
      display: grid;
      grid-template-columns: 1.3fr 1fr auto;
      gap: 10px;
      align-items: center;
    }

    .add-course-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(180px, 1fr));
      gap: 8px;
      align-items: end;
    }

    .semester-control-row {
      display: grid;
      grid-template-columns: 220px 1fr 180px;
      gap: 8px;
      align-items: center;
    }

    .button-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 6px;
    }

    .button-row button {
      width: auto;
      min-width: 150px;
    }

    .check-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      padding: 8px 10px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: #f9fafb;
      font-size: 13px;
      white-space: nowrap;
    }

    .check-row input {
      width: auto;
      margin: 0;
    }

    .compact-section {
      margin-bottom: 10px;
    }

    .muted { color: var(--muted); font-size: 13px; }
    .pill { display: inline-block; padding: 4px 8px; border-radius: 999px; background: #e5e7eb; font-size: 12px; margin: 3px; }

    .response-box {
      background: #111827;
      color: #d1fae5;
      padding: 12px;
      border-radius: 10px;
      overflow: auto;
      max-height: 360px;
      font-size: 12px;
      white-space: pre-wrap;
    }

    .term-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(360px, 1fr));
      gap: 10px;
      margin-top: 8px;
      align-items: start;
    }

    .term-box {
      min-height: 92px;
      border: 2px dashed #cbd5e1;
      border-radius: 12px;
      padding: 8px;
      background: #f9fafb;
      box-sizing: border-box;
    }

    .palette-box {
      min-height: 70px;
    }

    .term-box.special {
      background: #fefce8;
      border-color: #facc15;
    }

    .term-title {
      font-weight: bold;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }

    .course-card {
      background: #e0ecff;
      border: 1px solid #93c5fd;
      border-radius: 9px;
      padding: 6px 7px;
      margin: 5px 0;
      cursor: grab;
      display: grid;
      grid-template-columns: minmax(145px, 200px) minmax(220px, 1fr) auto;
      gap: 7px;
      align-items: center;
      width: 100%;
      box-sizing: border-box;
    }

    .card-choice-wrap {
      margin-top: 5px;
    }

    .card-choice-wrap label {
      display: block;
      font-size: 11px;
      color: #4b5563;
      margin-bottom: 2px;
    }

    .card-choice {
      margin: 0;
      padding: 5px 7px;
      font-size: 12px;
      background: white;
      max-width: 100%;
    }

    .completed-toggle {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: #374151;
      white-space: nowrap;
    }

    .completed-toggle input {
      width: auto;
      margin: 0;
    }

    .course-actions {
      display: flex;
      gap: 6px;
      justify-content: flex-end;
      flex-wrap: wrap;
    }

    .required-bank {
      position: sticky;
      top: 12px;
      max-height: calc(100vh - 100px);
      overflow: auto;
    }

    .required-group-title {
      margin: 10px 0 3px;
      font-weight: bold;
      font-size: 13px;
      color: #374151;
    }

    .course-card.completed {
      background: #dcfce7;
      border-color: #86efac;
    }

    .course-card.placeholder {
      background: #ede9fe;
      border-color: #c4b5fd;
    }

    .course-card .code {
      font-weight: bold;
    }

    .course-card .detail {
      color: #374151;
      font-size: 12px;
      margin-top: 3px;
    }

    .result-item {
      border-bottom: 1px solid #e5e7eb;
      padding: 9px;
      cursor: pointer;
    }

    .result-item:hover { background: #f3f4f6; }

    .scrollbox {
      max-height: 220px;
      overflow: auto;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: #fafafa;
    }

    .schedule-card {
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 12px;
      margin: 10px 0;
      background: white;
    }

    .schedule-terms {
      display: grid;
      grid-template-columns: repeat(2, minmax(220px, 1fr));
      gap: 8px;
      margin-top: 8px;
    }

    .term-summary {
      background: #f9fafb;
      border-radius: 8px;
      padding: 8px;
      font-size: 13px;
    }

    @media (max-width: 1150px) {
      .builder-workspace, .settings-grid, .add-course-grid, .semester-control-row {
        grid-template-columns: 1fr;
      }
      .required-bank {
        position: static;
        max-height: none;
      }
      .button-row button { width: 100%; }
    }

    @media (max-width: 900px) {
      .grid-2, .grid-3, .term-grid, .schedule-terms {
        grid-template-columns: 1fr;
      }

      .course-card {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
<header>
  <h1>BU Course Scheduler</h1>
  <nav>
    <a href="/login">Login</a>
    <a href="/build">Build My Schedule</a>
    <a href="/schedules">View Student Schedules</a>
    <button onclick="quickMe()">Current User</button>
    <span class="pill" id="cookieStatus">Checking session...</span>
  </nav>
</header>

<main>
  {{ content|safe }}
</main>

<script>
const MAJOR_DATA = {{ major_data|safe }};
const TERM_LABELS = {{ term_labels|safe }};

function showResponse(data, boxId="responseBox") {
  const box = document.getElementById(boxId);
  if (!box) return;
  box.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

async function api(method, path, body=null) {
  const opts = { method, headers: {"Content-Type": "application/json"}, credentials: "same-origin" };
  if (body !== null) opts.body = JSON.stringify(body);
  const res = await fetch("/proxy" + path, opts);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  showResponse({status: res.status, data});
  await checkSession(false);
  return {status: res.status, data};
}

async function checkSession(show=false) {
  const res = await fetch("/session-status", {credentials:"same-origin"});
  const data = await res.json();
  const el = document.getElementById("cookieStatus");
  if (el) el.textContent = data.hasBackendCookies ? "Logged-in cookie stored" : "No login cookie stored";
  if (show) showResponse(data);
  return data;
}

async function quickMe() {
  await api("GET", "/api/auth/me");
}

window.addEventListener("load", () => checkSession(false));
</script>

{{ script|safe }}
</body>
</html>
"""

LOGIN_CONTENT = r"""
<div class="grid-2">
  <div>
    <section>
      <h2>Login</h2>
      <input id="loginEmail" placeholder="email@bu.edu">
      <input id="loginPassword" type="password" placeholder="password">
      <button onclick="loginUser()">Login</button>
      <button class="secondary" onclick="logoutUser()">Logout</button>
      <button class="secondary" onclick="quickMe()">Get Current User</button>
    </section>

    <section>
      <h2>Register</h2>
      <input id="registerEmail" placeholder="email@bu.edu">
      <input id="registerPassword" type="password" placeholder="password">
      <input id="registerName" placeholder="display name">
      <button onclick="registerUser()">Register</button>

      <h3>Verify Email</h3>
      <input id="verifyEmail" placeholder="email@bu.edu">
      <input id="verifyCode" placeholder="6 digit code">
      <button onclick="verifyEmail()">Verify</button>
      <button class="secondary" onclick="resendVerificationCode()">Resend Code</button>
    </section>
  </div>

  <div>
    <section>
      <h2>Forgot Password</h2>
      <input id="forgotEmail" placeholder="email@bu.edu">
      <button onclick="forgotPassword()">Send Reset Code</button>

      <h3>Reset Password</h3>
      <input id="resetEmail" placeholder="email@bu.edu">
      <input id="resetCode" placeholder="6 digit reset code">
      <input id="newPassword" type="password" placeholder="new password">
      <button class="success" onclick="resetPassword()">Reset Password</button>
    </section>

    <section>
      <h2>Response</h2>
      <pre id="responseBox" class="response-box">No response yet.</pre>
    </section>
  </div>
</div>
"""

LOGIN_SCRIPT = r"""
<script>
function saveEmailFields() {
  ["loginEmail","registerEmail","verifyEmail","forgotEmail","resetEmail"].forEach(id => {
    const el = document.getElementById(id);
    if (el) localStorage.setItem(id, el.value || "");
  });
}

function loadEmailFields() {
  ["loginEmail","registerEmail","verifyEmail","forgotEmail","resetEmail"].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = localStorage.getItem(id) || "";
    el.addEventListener("input", saveEmailFields);
  });
}

async function registerUser() {
  const email = document.getElementById("registerEmail").value.trim();
  const password = document.getElementById("registerPassword").value;
  const displayName = document.getElementById("registerName").value.trim();
  document.getElementById("verifyEmail").value = email;
  document.getElementById("loginEmail").value = email;
  saveEmailFields();
  await api("POST", "/api/auth/register", { email, password, displayName });
}

async function resendVerificationCode() {
  const email = document.getElementById("verifyEmail").value.trim() || document.getElementById("registerEmail").value.trim();
  await api("POST", "/api/auth/resend-verification-code", { email });
}

async function verifyEmail() {
  await api("POST", "/api/auth/verify-email", {
    email: document.getElementById("verifyEmail").value.trim(),
    code: document.getElementById("verifyCode").value.trim()
  });
}

async function loginUser() {
  saveEmailFields();
  await api("POST", "/api/auth/login", {
    email: document.getElementById("loginEmail").value.trim(),
    password: document.getElementById("loginPassword").value
  });
}

async function logoutUser() {
  await api("POST", "/api/auth/logout");
  await fetch("/clear-session", {method:"POST", credentials:"same-origin"});
  await checkSession(false);
}

async function forgotPassword() {
  const email = document.getElementById("forgotEmail").value.trim();
  document.getElementById("resetEmail").value = email;
  saveEmailFields();
  await api("POST", "/api/auth/forgot-password", { email });
}

async function resetPassword() {
  await api("POST", "/api/auth/reset-password", {
    email: document.getElementById("resetEmail").value.trim(),
    code: document.getElementById("resetCode").value.trim(),
    newPassword: document.getElementById("newPassword").value
  });
}

window.addEventListener("load", loadEmailFields);
</script>
"""

BUILD_CONTENT = r"""
<div class="builder-page">
  <section class="builder-top">
    <div>
      <h2>My Schedule Settings</h2>
      <div class="settings-grid">
        <input id="scheduleTitle" value="My Four-Year Plan" placeholder="Schedule title">
        <select id="scheduleMajor" onchange="majorChanged()"></select>
        <label class="check-row">
          <input id="scheduleCompleted" type="checkbox">
          <span>I am done with college / this plan is complete</span>
        </label>
      </div>
      <textarea id="scheduleComments" placeholder="Schedule notes">Built in the unified Flask schedule builder.</textarea>
      <div class="button-row">
        <button class="success" onclick="saveSchedule()">Save/Update My Schedule</button>
        <button class="secondary" onclick="loadMySchedule()">Load My Existing Schedule</button>
        <button class="secondary" onclick="loadRequiredPlan()">Refresh Required List</button>
        <button class="secondary" onclick="previewSchedule()">Preview JSON</button>
      </div>
    </div>
  </section>

  <div class="builder-workspace">
    <div class="schedule-side">
      <section class="compact-section">
        <h2>Add Course</h2>
        <div class="add-course-grid">
          <div>
            <label>Requirement type</label>
            <select id="requirementType" onchange="requirementTypeChanged()"></select>
          </div>
          <div>
            <label>Approved elective/core choice</label>
            <select id="electiveChoiceSelect" onchange="electiveChoiceChanged()">
              <option value="">Pick a requirement type first</option>
            </select>
            <div class="muted" id="electiveChoiceHint">Pick a requirement type first. Options come from the selected major's planning sheet.</div>
          </div>
          <div>
            <label>Manual course code or placeholder</label>
            <input id="manualCourseCode" placeholder="Example: ENG EC 327 or Technical Elective">
          </div>
          <div>
            <label>Course note</label>
            <input id="manualCourseComment" placeholder="Optional comment">
          </div>
        </div>
        <div class="button-row">
          <button onclick="addManualCourse()">Add to Course Palette</button>
          <button class="secondary" onclick="searchCourses()">Search BU Course Data</button>
        </div>
        <input id="courseQuery" placeholder="Search course, instructor, Hub, status...">
        <div id="courseResults" class="scrollbox"><div class="muted" style="padding:8px;">Course search results appear here.</div></div>
      </section>

      <section class="compact-section">
        <h2>Course Palette</h2>
        <p class="muted">Drag cards into semesters or into Completed / Transferred.</p>
        <div id="coursePalette" class="term-box palette-box" ondrop="dropCourse(event)" ondragover="allowDrop(event)"></div>
      </section>

      <section class="compact-section">
        <h2>Semester Controls</h2>
        <div class="semester-control-row">
          <select id="newTermLabel"></select>
          <input id="newTermCustom" placeholder="Optional custom label, e.g. Fifth Year Fall">
          <button onclick="addTermBox()">Add Semester Box</button>
        </div>
        <p class="muted">Only cards placed in semester boxes are saved. The right-side required list hides courses already placed.</p>
      </section>

      <section class="compact-section">
        <h2>My Schedule Builder</h2>
        <div id="termGrid" class="term-grid"></div>
      </section>

      <section class="compact-section">
        <h2>Response</h2>
        <pre id="responseBox" class="response-box">No response yet.</pre>
      </section>
    </div>

    <aside class="required-side">
      <section class="required-bank">
        <h2>Required Courses</h2>
        <p class="muted">Drag these into semesters. Already-placed requirements are hidden here.</p>
        <div id="requiredCourseBank"></div>
      </section>
    </aside>
  </div>
</div>
"""

BUILD_SCRIPT = r"""
<script>
let nextCardId = 1;

function setupBuilder() {
  const majorSelect = document.getElementById("scheduleMajor");
  majorSelect.innerHTML = "";
  Object.keys(MAJOR_DATA).forEach(major => {
    const opt = document.createElement("option");
    opt.value = major;
    opt.textContent = major;
    majorSelect.appendChild(opt);
  });

  const newTerm = document.getElementById("newTermLabel");
  TERM_LABELS.forEach(t => {
    const opt = document.createElement("option");
    opt.value = t;
    opt.textContent = t;
    newTerm.appendChild(opt);
  });

  ensureTermBox("Completed / Transferred", true);
  ["Freshman Fall","Freshman Spring","Sophomore Fall","Sophomore Spring","Junior Fall","Junior Spring","Senior Fall","Senior Spring"].forEach(t => ensureTermBox(t));
  majorChanged();
}

function majorChanged() {
  updateRequirementDropdown();
  refreshCardChoiceDropdowns();
  loadRequiredPlan();
}

function refreshCardChoiceDropdowns() {
  // Rebuild card dropdowns when the user switches majors so CE Core, EE Core,
  // Technical Elective, etc. always use the currently selected planning sheet.
  const cards = [...document.querySelectorAll(".course-card")];
  cards.forEach(card => {
    const course = {
      course_code: card.dataset.code,
      comments: card.dataset.comments,
      requirement_type: card.dataset.requirementType,
      selected_course_code: card.dataset.selectedCourse,
      source_term: card.dataset.sourceTerm,
      status: card.dataset.status,
      completed: card.dataset.completed
    };
    const fresh = makeCourseCard(course);
    card.replaceWith(fresh);
  });
}

function updateRequirementDropdown() {
  const major = document.getElementById("scheduleMajor").value;
  const req = document.getElementById("requirementType");
  req.innerHTML = "";
  ["Regular Course", "Hub Elective"].concat(Object.keys(MAJOR_DATA[major]?.dropdowns || {})).forEach(type => {
    if ([...req.options].some(o => o.value === type)) return;
    const opt = document.createElement("option");
    opt.value = type;
    opt.textContent = type;
    req.appendChild(opt);
  });
  requirementTypeChanged();
}

function requirementTypeChanged() {
  const major = document.getElementById("scheduleMajor").value;
  const type = document.getElementById("requirementType").value;
  const select = document.getElementById("electiveChoiceSelect");
  const hint = document.getElementById("electiveChoiceHint");

  select.innerHTML = "";

  const options = (MAJOR_DATA[major]?.dropdowns || {})[type] || [];

  if (!options.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No approved list for this type";
    select.appendChild(opt);
    hint.textContent = "No program-sheet option list for this type. Use the manual course code box.";
    return;
  }

  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = `Select ${type}...`;
  select.appendChild(blank);

  hint.textContent = `${options.length} approved option(s) loaded for ${type}. Select one from the dropdown.`;

  options.forEach(o => {
    const opt = document.createElement("option");
    opt.value = o;
    opt.textContent = o;
    select.appendChild(opt);
  });
}

function electiveChoiceChanged() {
  const type = document.getElementById("requirementType").value;
  const selected = document.getElementById("electiveChoiceSelect").value.trim();
  if (!selected) return;

  const code = parseCourseCode(selected);
  if (type.includes("Elective") || type.includes("Core") || type.includes("Breadth") || type.includes("Fields") || type.includes("Professional")) {
    document.getElementById("manualCourseCode").value = `${type} (${code})`;
    document.getElementById("manualCourseComment").value = selected;
  } else {
    document.getElementById("manualCourseCode").value = code;
    document.getElementById("manualCourseComment").value = selected;
  }
}

function parseCourseCode(selected) {
  const firstPart = String(selected).split(" - ")[0].trim();
  const match = firstPart.match(/[A-Z]{2,4}\s+[A-Z]{0,3}\s*\d{3}[A-Z]?/);
  return match ? match[0].replace(/\s+/g, " ").trim() : firstPart;
}

function ensureTermBox(termName, special=false) {
  if (document.querySelector(`.term-box[data-term="${cssEscape(termName)}"]`)) return;
  const grid = document.getElementById("termGrid");
  const box = document.createElement("div");
  box.className = "term-box" + (special ? " special" : "");
  box.dataset.term = termName;
  box.ondragover = allowDrop;
  box.ondrop = dropCourse;
  box.innerHTML = `<div class="term-title"><span>${escapeHtml(termName)}</span><button class="small danger" onclick="removeTermBox(event, this)">Remove</button></div>`;
  grid.appendChild(box);
}

function removeTermBox(event, button) {
  event.stopPropagation();
  const box = button.closest(".term-box");
  const term = box.dataset.term;
  if (term === "Completed / Transferred") {
    alert("Completed / Transferred cannot be removed.");
    return;
  }
  document.getElementById("coursePalette").append(...box.querySelectorAll(".course-card"));
  box.remove();
  loadRequiredPlan();
}

function addTermBox() {
  const custom = document.getElementById("newTermCustom").value.trim();
  const label = custom || document.getElementById("newTermLabel").value;
  ensureTermBox(label);
  document.getElementById("newTermCustom").value = "";
}

function loadRequiredPlan() {
  const major = document.getElementById("scheduleMajor").value;
  const plan = MAJOR_DATA[major]?.required_plan || {};
  const bank = document.getElementById("requiredCourseBank");
  if (!bank) return;

  // Count cards that are already placed in the user schedule. This prevents the
  // right-side required-course bank from repeatedly showing requirements that the
  // user has already dragged into a semester or Completed / Transferred.
  const used = getPlacedRequirementCounts();

  bank.innerHTML = "";
  Object.entries(plan).forEach(([term, courses]) => {
    ensureTermBox(term);
    const group = document.createElement("div");
    group.className = "required-group";
    group.innerHTML = `<div class="required-group-title">${escapeHtml(term)}</div>`;

    let visibleCount = 0;
    courses.forEach(([code, comment]) => {
      const key = requirementKeyFromCode(code);
      if ((used[key] || 0) > 0) {
        used[key] -= 1;
        return;
      }
      group.appendChild(makeCourseCard({
        course_code: code,
        comments: comment,
        requirement_type: inferType(code),
        source_term: term
      }));
      visibleCount += 1;
    });

    if (visibleCount > 0) bank.appendChild(group);
  });

  if (!bank.children.length) {
    bank.innerHTML = `<div class="muted" style="padding:8px;">All required courses for this major are already placed in your schedule boxes.</div>`;
  }
}

function inferType(code) {
  if (code.includes("Elective")) return code;
  return "Required Course";
}

function requirementKeyFromCode(code) {
  const raw = String(code || "").trim();
  // A placed elective like "Technical Elective (ENG EC 414)" should count as a
  // Technical Elective requirement from the planning sheet.
  const parenIndex = raw.indexOf("(");
  const base = parenIndex >= 0 ? raw.slice(0, parenIndex).trim() : raw;
  return base.replace(/\s+/g, " ").toUpperCase();
}

function getPlacedRequirementCounts() {
  const counts = {};
  document.querySelectorAll("#termGrid .course-card").forEach(card => {
    const key = requirementKeyFromCode(card.dataset.code || "");
    if (!key) return;
    counts[key] = (counts[key] || 0) + 1;
  });
  return counts;
}

function baseRequirementTypeFromCourse(course) {
  const code = String(course.course_code || "").trim();
  const type = String(course.requirement_type || "").trim();

  if (type && type !== "Required Course" && type !== "Searched Course") return type;

  const parenIndex = code.indexOf("(");
  const base = parenIndex >= 0 ? code.slice(0, parenIndex).trim() : code;

  // These are the program-planning-sheet requirement labels that should expose
  // a major-specific chooser directly on the card.
  if (base.includes("Elective") || base.includes("Core") || base.includes("Breadth") || base.includes("Fields") || base.includes("Professional")) {
    return base;
  }

  return type || "Required Course";
}

function optionListForType(type) {
  const major = document.getElementById("scheduleMajor")?.value || Object.keys(MAJOR_DATA)[0];
  return (MAJOR_DATA[major]?.dropdowns || {})[type] || [];
}

function makeCardChoiceHtml(cardId, type, selectedValue) {
  const options = optionListForType(type);
  if (!options.length) return "";

  const selected = selectedValue || "";
  const selectOptions = [`<option value="">Select ${escapeHtml(type)}...</option>`].concat(
    options.map(o => `<option value="${escapeHtml(o)}" ${o === selected ? "selected" : ""}>${escapeHtml(o)}</option>`)
  ).join("");
  return `
    <div class="card-choice-wrap">
      <label>${escapeHtml(type)} choice</label>
      <select class="card-choice" onmousedown="event.stopPropagation()" onclick="event.stopPropagation()" onchange="cardChoiceChanged(event, this)">${selectOptions}</select>
    </div>
  `;
}

function cardChoiceChanged(event, input) {
  event.stopPropagation();
  const card = input.closest(".course-card");
  const selected = input.value.trim();
  const type = card.dataset.requirementType || requirementKeyFromCode(card.dataset.code || "");

  if (!selected) return;

  const selectedCode = parseCourseCode(selected);
  card.dataset.code = `${type} (${selectedCode})`;
  card.dataset.comments = selected;
  card.dataset.selectedCourse = selectedCode;

  const codeEl = card.querySelector(".code");
  const commentEl = card.querySelector(".comment-text");
  if (codeEl) codeEl.textContent = card.dataset.code;
  if (commentEl) commentEl.textContent = selected;

  loadRequiredPlan();
}

function makeCourseCard(course) {
  const card = document.createElement("div");
  card.className = "course-card";
  const isCompleted = course.completed === true || course.completed === "true" || (course.status || "").toLowerCase().includes("completed") || (course.status || "").toLowerCase().includes("transferred");
  if (isCompleted) card.classList.add("completed");
  if ((course.course_code || "").includes("Elective")) card.classList.add("placeholder");

  card.id = "course-" + nextCardId++;
  card.draggable = true;
  card.ondragstart = dragCourse;
  card.dataset.code = course.course_code || "";
  card.dataset.comments = course.comments || "";
  card.dataset.requirementType = baseRequirementTypeFromCourse(course);
  card.dataset.selectedCourse = course.selected_course_code || "";
  card.dataset.sourceTerm = course.source_term || "";
  card.dataset.completed = isCompleted ? "true" : "false";
  card.dataset.status = isCompleted ? "completed/transferred" : (course.status || "planned");

  const choiceValue = course.comments || "";
  const choiceHtml = makeCardChoiceHtml(card.id, card.dataset.requirementType, choiceValue);

  card.innerHTML = `
    <div>
      <div class="code">${escapeHtml(card.dataset.code)}</div>
      <div class="detail">${escapeHtml(card.dataset.requirementType || "Course")}</div>
    </div>
    <div class="detail">
      <span class="comment-text">${escapeHtml(card.dataset.comments)}</span><br>
      Status: <span class="status-text">${escapeHtml(card.dataset.status)}</span>
      ${choiceHtml}
    </div>
    <div class="course-actions">
      <label class="completed-toggle" onclick="event.stopPropagation()">
        <input type="checkbox" ${card.dataset.completed === "true" ? "checked" : ""} onchange="toggleCompleted(event, this)">
        Done
      </label>
      <button class="small success" onclick="markCompleted(event, this)">Move to Completed</button>
      <button class="small danger" onclick="removeCard(event, this)">Remove</button>
    </div>
  `;
  return card;
}

function addManualCourse() {
  const type = document.getElementById("requirementType").value;
  const selected = document.getElementById("electiveChoiceSelect").value.trim();
  let code = document.getElementById("manualCourseCode").value.trim();
  const comments = document.getElementById("manualCourseComment").value.trim();

  if (!code && selected) {
    const selectedCode = parseCourseCode(selected);
    code = `${type} (${selectedCode})`;
  }
  if (!code) { alert("Enter a course code or select an elective option."); return; }

  const selectedCode = selected ? parseCourseCode(selected) : "";
  document.getElementById("coursePalette").appendChild(makeCourseCard({
    course_code: code,
    comments,
    requirement_type: type,
    selected_course_code: selectedCode
  }));

  document.getElementById("manualCourseCode").value = "";
  document.getElementById("manualCourseComment").value = "";
  document.getElementById("electiveChoiceSelect").value = "";
}

function setCardCompleted(card, completed) {
  card.dataset.completed = completed ? "true" : "false";
  card.dataset.status = completed ? "completed/transferred" : "planned";
  card.classList.toggle("completed", completed);
  const detail = card.querySelector(".status-text");
  if (detail) detail.textContent = card.dataset.status;
}

function toggleCompleted(event, checkbox) {
  event.stopPropagation();
  const card = checkbox.closest(".course-card");
  setCardCompleted(card, checkbox.checked);
  loadRequiredPlan();
}

function markCompleted(event, button) {
  event.stopPropagation();
  const card = button.closest(".course-card");
  setCardCompleted(card, true);
  const cb = card.querySelector(".completed-toggle input");
  if (cb) cb.checked = true;
  const completedBox = document.querySelector(`.term-box[data-term="Completed / Transferred"]`);
  completedBox.appendChild(card);
  loadRequiredPlan();
}

function removeCard(event, button) {
  event.stopPropagation();
  button.closest(".course-card").remove();
  loadRequiredPlan();
}

function dragCourse(event) {
  event.dataTransfer.setData("text/plain", event.target.id);
}

function allowDrop(event) {
  event.preventDefault();
}

function dropCourse(event) {
  event.preventDefault();
  const id = event.dataTransfer.getData("text/plain");
  const card = document.getElementById(id);
  if (card) {
    event.currentTarget.appendChild(card);
    loadRequiredPlan();
  }
}

function buildScheduleJson() {
  const title = document.getElementById("scheduleTitle").value.trim();
  const major = document.getElementById("scheduleMajor").value;
  const completed = document.getElementById("scheduleCompleted")?.checked || false;
  const comments = document.getElementById("scheduleComments").value.trim();
  const terms = {};

  document.querySelectorAll("#termGrid .term-box").forEach(box => {
    const term = box.dataset.term;
    if (term === "Required Courses") return;
    terms[term] = [];
    box.querySelectorAll(".course-card").forEach(card => {
      terms[term].push({
        course_code: card.dataset.code,
        comments: card.dataset.comments || "",
        requirement_type: card.dataset.requirementType || "",
        selected_course_code: card.dataset.selectedCourse || "",
        source_term: card.dataset.sourceTerm || "",
        status: card.dataset.status || "planned",
        completed: card.dataset.completed === "true"
      });
    });
  });

  return { title, major, completed, comments, terms };
}

function previewSchedule() {
  showResponse(buildScheduleJson());
}

async function saveSchedule() {
  const schedule = buildScheduleJson();
  if (!schedule.title) { alert("Title required."); return; }
  await api("POST", "/api/schedules", schedule);
}

async function loadMySchedule() {
  const result = await api("GET", "/api/my-schedule");
  const schedule = result.data?.schedule || result.data?.data?.schedule;
  if (!schedule) { alert("No saved schedule found."); return; }
  renderSchedule(schedule);
}

function renderSchedule(schedule) {
  document.getElementById("scheduleTitle").value = schedule.title || "";
  document.getElementById("scheduleMajor").value = schedule.major || Object.keys(MAJOR_DATA)[0];
  document.getElementById("scheduleCompleted").checked = !!schedule.completed;
  document.getElementById("scheduleComments").value = schedule.comments || "";
  updateRequirementDropdown();

  document.getElementById("termGrid").innerHTML = "";
  ensureTermBox("Completed / Transferred", true);

  Object.entries(schedule.terms || {}).forEach(([term, courses]) => {
    if (term === "Required Courses") return;
    ensureTermBox(term, term === "Completed / Transferred");
    const box = document.querySelector(`.term-box[data-term="${cssEscape(term)}"]`);
    courses.forEach(c => box.appendChild(makeCourseCard(c)));
  });
  loadRequiredPlan();
}

async function searchCourses() {
  const q = document.getElementById("courseQuery").value.trim();
  const result = await api("GET", "/api/courses?q=" + encodeURIComponent(q));
  const container = document.getElementById("courseResults");
  container.innerHTML = "";
  const courses = result.data?.results || result.data?.data?.results || [];
  if (!Array.isArray(courses) || !courses.length) {
    container.innerHTML = `<div class="muted" style="padding:8px;">No results.</div>`;
    return;
  }
  courses.slice(0, 50).forEach(course => {
    const div = document.createElement("div");
    div.className = "result-item";
    const code = course.course_code || "";
    const title = course.course_title || course.hub?.name || "";
    div.innerHTML = `<b>${escapeHtml(code)}</b><br>${escapeHtml(title)}<br><span class="muted">${escapeHtml(course.instructor || "")} ${escapeHtml(course.status || "")}</span>`;
    div.onclick = () => document.getElementById("coursePalette").appendChild(makeCourseCard({
      course_code: code,
      comments: title,
      requirement_type: "Searched Course"
    }));
    container.appendChild(div);
  });
}

function cssEscape(s) {
  return String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

function escapeHtml(str) {
  return String(str || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

window.addEventListener("load", setupBuilder);
</script>
"""

SCHEDULES_CONTENT = r"""
<section>
  <h2>View Student Schedules</h2>
  <div class="grid-3">
    <select id="filterMajor"></select>
    <input id="filterText" placeholder="Filter by student, course, comment, semester...">
    <button onclick="loadSchedules()">Load / Filter Schedules</button>
  </div>
</section>

<section>
  <h2>Results</h2>
  <div id="scheduleResults" class="scrollbox" style="max-height: none; padding: 10px;">Click Load / Filter Schedules.</div>
</section>

<section>
  <h2>Response</h2>
  <pre id="responseBox" class="response-box">No response yet.</pre>
</section>
"""

SCHEDULES_SCRIPT = r"""
<script>
function setupScheduleFilters() {
  const major = document.getElementById("filterMajor");
  major.innerHTML = `<option value="">All majors</option>`;
  Object.keys(MAJOR_DATA).forEach(m => {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m;
    major.appendChild(opt);
  });
}

async function loadSchedules() {
  const result = await api("GET", "/api/schedules");
  const schedules = result.data?.data || result.data || [];
  renderSchedules(Array.isArray(schedules) ? schedules : []);
}

function renderSchedules(schedules) {
  const majorFilter = document.getElementById("filterMajor").value.toLowerCase();
  const text = document.getElementById("filterText").value.toLowerCase();
  const container = document.getElementById("scheduleResults");
  container.innerHTML = "";

  const filtered = schedules.filter(s => {
    const haystack = JSON.stringify(s).toLowerCase();
    const okMajor = !majorFilter || String(s.major || "").toLowerCase() === majorFilter;
    const okText = !text || haystack.includes(text);
    return okMajor && okText;
  });

  if (!filtered.length) {
    container.innerHTML = `<div class="muted">No matching schedules found.</div>`;
    return;
  }

  filtered.forEach(s => {
    const card = document.createElement("div");
    card.className = "schedule-card";
    const creator = s.creator?.displayName || s.creator?.email || "Unknown student";
    const terms = s.terms || {};
    const termHtml = Object.entries(terms).map(([term, courses]) => {
      const list = (courses || []).map(c => `<li>${escapeHtml(c.course_code)} ${c.status ? `<span class="muted">(${escapeHtml(c.status)})</span>` : ""}</li>`).join("");
      return `<div class="term-summary"><b>${escapeHtml(term)}</b><ul>${list || "<li class='muted'>No courses</li>"}</ul></div>`;
    }).join("");

    card.innerHTML = `
      <h3>${escapeHtml(s.title || "Untitled Schedule")}</h3>
      <div class="muted">Student: ${escapeHtml(creator)} | Major: ${escapeHtml(s.major || "Unspecified")} | Completed college/plan: ${s.completed ? "Yes" : "No"}</div>
      <p>${escapeHtml(s.comments || "")}</p>
      <div class="schedule-terms">${termHtml}</div>
      <button class="secondary" onclick='showResponse(${JSON.stringify(JSON.stringify(s, null, 2))})'>Show Raw JSON</button>
    `;
    container.appendChild(card);
  });
}

function escapeHtml(str) {
  return String(str || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

window.addEventListener("load", setupScheduleFilters);
</script>
"""


def render_page(content, script=""):
    import json
    return render_template_string(
        BASE_HTML,
        content=content,
        script=script,
        major_data=json.dumps(MAJOR_DATA),
        term_labels=json.dumps(TERM_LABELS),
    )


@app.route("/")
def root():
    return redirect("/login")


@app.route("/login")
def login_page():
    return render_page(LOGIN_CONTENT, LOGIN_SCRIPT)


@app.route("/build")
def build_page():
    return render_page(BUILD_CONTENT, BUILD_SCRIPT)


@app.route("/schedules")
def schedules_page():
    return render_page(SCHEDULES_CONTENT, SCHEDULES_SCRIPT)


@app.route("/program-data")
def program_data():
    return jsonify({"majors": MAJOR_DATA, "termLabels": TERM_LABELS})


@app.route("/session-status")
def session_status():
    cookies = flask_session.get("backend_cookies", {})
    return jsonify({
        "hasBackendCookies": bool(cookies),
        "backendCookieNames": list(cookies.keys()),
        "note": "Cookies are stored per browser in Flask's signed session cookie.",
    })


@app.route("/clear-session", methods=["POST"])
def clear_session():
    flask_session.pop("backend_cookies", None)
    flask_session.modified = True
    return jsonify({"message": "Cleared Flask-stored backend cookies."})


@app.route("/proxy/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    backend_path = "/" + path
    url = BACKEND_URL + backend_path
    backend_session = make_backend_session()

    try:
        response = backend_session.request(
            request.method,
            url,
            params=request.args if request.method == "GET" else None,
            json=request.get_json(silent=True) if request.method in ["POST", "PUT", "DELETE"] else None,
            timeout=30,
        )

        save_backend_cookies(backend_session)

        if path == "api/auth/logout" and request.method == "POST" and response.status_code < 400:
            flask_session.pop("backend_cookies", None)
            flask_session.modified = True

        try:
            return jsonify(response.json()), response.status_code
        except Exception:
            return response.text, response.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Could not connect to backend.",
            "detail": f"Make sure your Node backend is running at {BACKEND_URL}."
        }), 502

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Backend request timed out.",
            "detail": "The backend did not respond before the Flask proxy timeout."
        }), 504

    except Exception as e:
        return jsonify({
            "error": "Proxy error.",
            "detail": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", debug=True, port=port)
