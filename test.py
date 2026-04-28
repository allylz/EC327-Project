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
    "Transferred Courses",
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
      --bg: #f8fafc;
      --panel: #ffffff;
      --ink: #0f172a;
      --muted: #64748b;
      --line: #e2e8f0;
      --blue: #2563eb;
      --blue-dark: #1d4ed8;
      --green: #059669;
      --red: #dc2626;
      --amber: #f59e0b;
      --soft-blue: #eff6ff;
      --soft-green: #ecfdf5;
      --soft-purple: #f5f3ff;
      --soft-yellow: #fffbeb;
      --shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }

    header {
      position: sticky;
      top: 0;
      z-index: 100;
      background: #0f172a;
      color: white;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    .header-inner {
      width: 100%;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
    }

    .brand {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .brand h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.1;
      letter-spacing: -0.02em;
    }

    .brand .subtitle {
      color: #cbd5e1;
      font-size: 12px;
    }

    nav {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
    }

    nav a, nav button {
      color: white;
      background: rgba(255,255,255,0.10);
      text-decoration: none;
      padding: 8px 11px;
      border-radius: 7px;
      border: 1px solid rgba(255,255,255,0.12);
      cursor: pointer;
      font-size: 13px;
      font-weight: 700;
      width: auto;
      margin: 0;
    }

    nav a:hover, nav button:hover {
      background: rgba(255,255,255,0.18);
    }

    .hello-pill {
      color: #e2e8f0;
      font-size: 13px;
      padding: 8px 10px;
      background: rgba(15, 23, 42, 0.3);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 7px;
      max-width: 280px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    main {
      padding: 12px;
      max-width: none;
      width: 100%;
      margin: 0;
    }

    section, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px;
      box-shadow: var(--shadow);
      margin-bottom: 12px;
    }

    h2 { margin: 0 0 10px; font-size: 18px; letter-spacing: -0.01em; }
    h3 { margin: 10px 0 6px; font-size: 14px; }
    label { font-size: 12px; color: #475569; font-weight: 700; }

    input, textarea, button, select {
      width: 100%;
      padding: 8px 9px;
      margin: 4px 0;
      border-radius: 7px;
      border: 1px solid var(--line);
      font-size: 14px;
      background: white;
    }

    textarea { min-height: 58px; resize: vertical; }

    button {
      background: var(--blue);
      color: white;
      font-weight: 800;
      border: none;
      cursor: pointer;
    }

    button:hover { background: var(--blue-dark); }
    button.secondary { background: #475569; }
    button.success { background: var(--green); }
    button.danger { background: var(--red); }
    button.small { width: auto; padding: 5px 8px; font-size: 11px; margin: 2px; }

    .grid-2 {
      display: grid;
      grid-template-columns: minmax(300px, 420px) 1fr;
      gap: 14px;
      align-items: start;
    }

    .grid-3 {
      display: grid;
      grid-template-columns: 260px 1fr 190px;
      gap: 10px;
      align-items: end;
    }

    .builder-page {
      width: calc(100vw - 24px);
      max-width: none;
      margin-left: calc(50% - 50vw + 12px);
      margin-right: calc(50% - 50vw + 12px);
    }

    .builder-top { margin-bottom: 10px; }

    .builder-workspace {
      width: 100%;
      padding-right: 392px;
      box-sizing: border-box;
    }

    .schedule-side { min-width: 0; }

    .required-side {
      position: fixed;
      top: 78px;
      right: 10px;
      width: 360px;
      max-width: calc(100vw - 24px);
      z-index: 50;
      transition: transform 0.25s ease;
    }

    .required-side.collapsed {
      transform: translateX(calc(100% - 42px));
    }

    .required-toggle {
      position: absolute;
      left: -38px;
      top: 12px;
      width: 38px;
      min-width: 38px;
      height: 44px;
      border-radius: 8px 0 0 8px;
      padding: 0;
      font-size: 11px;
      writing-mode: vertical-rl;
      text-orientation: mixed;
      z-index: 51;
    }

    .hub-check-panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #f8fafc;
      margin-top: 8px;
    }

    .hub-check-panel h3 { margin: 0 0 4px; font-size: 15px; }

    .hub-check-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(225px, 1fr));
      gap: 6px;
      margin-top: 8px;
    }

    .hub-check-grid label {
      display: flex;
      align-items: center;
      gap: 7px;
      padding: 6px 8px;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: white;
      font-size: 12px;
      font-weight: 600;
    }

    .hub-check-grid input { width: auto; margin: 0; }

    .settings-grid {
      display: grid;
      grid-template-columns: 1.35fr 1fr;
      gap: 10px;
      align-items: center;
    }

    .add-course-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(170px, 1fr));
      gap: 8px;
      align-items: end;
    }

    .semester-control-row {
      display: grid;
      grid-template-columns: 220px 1fr 170px;
      gap: 8px;
      align-items: center;
    }

    .button-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
    .button-row button { width: auto; min-width: 145px; }

    .compact-section { margin-bottom: 10px; }
    .muted { color: var(--muted); font-size: 13px; }
    .pill { display: inline-block; padding: 4px 8px; border-radius: 999px; background: #e2e8f0; font-size: 12px; margin: 3px; }

    .term-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 10px;
      margin-top: 8px;
      align-items: start;
    }

    .term-box {
      min-height: 96px;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #f8fafc;
      box-sizing: border-box;
      display: flex;
      flex-wrap: wrap;
      align-items: flex-start;
      gap: 8px;
      width: 100%;
    }

    .palette-box { min-height: 74px; }
    .term-box.special { background: var(--soft-yellow); border-color: #fcd34d; }

    .term-title {
      font-weight: 900;
      color: #1e293b;
      margin-bottom: 2px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex: 0 0 100%;
      width: 100%;
      padding-bottom: 6px;
      border-bottom: 1px solid #e2e8f0;
    }

    .course-card {
      background: white;
      border: 1px solid #bfdbfe;
      border-left: 4px solid var(--blue);
      border-radius: 8px;
      padding: 8px;
      margin: 0;
      cursor: grab;
      display: grid;
      grid-template-rows: auto auto auto;
      gap: 6px;
      flex: 0 0 285px;
      width: 285px;
      max-width: 285px;
      min-height: 118px;
      box-sizing: border-box;
      box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
    }

    .course-card .code { font-weight: 900; font-size: 14px; color: #0f172a; }
    .course-card .detail { color: #475569; font-size: 12px; line-height: 1.25; }
    .comment-text { display: inline-block; max-height: 36px; overflow: auto; }

    .course-card.completed {
      background: var(--soft-green);
      border-color: #86efac;
      border-left-color: var(--green);
    }

    .course-card.placeholder {
      background: var(--soft-purple);
      border-color: #c4b5fd;
      border-left-color: #7c3aed;
    }

    .course-actions { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 5px; }

    .card-choice-wrap { margin-top: 5px; }
    .card-choice-wrap label { display: block; font-size: 11px; color: #475569; margin-bottom: 2px; }
    .card-choice { margin: 0; padding: 5px 7px; font-size: 12px; background: white; max-width: 100%; }

    .completed-toggle {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      color: #334155;
      white-space: nowrap;
    }

    .completed-toggle input { width: auto; margin: 0; }

    .required-bank {
      max-height: calc(100vh - 104px);
      overflow: auto;
      border: 1px solid var(--line);
      box-shadow: 0 14px 32px rgba(15, 23, 42, 0.14);
    }

    .required-group-title { margin: 10px 0 4px; font-weight: 900; font-size: 13px; color: #334155; }

    .required-bank .course-card {
      width: 100%;
      max-width: 100%;
      flex-basis: auto;
      min-height: 100px;
      margin-bottom: 7px;
    }

    .result-item { border-bottom: 1px solid #e5e7eb; padding: 9px; cursor: pointer; }
    .result-item:hover { background: #f1f5f9; }

    .scrollbox {
      max-height: 240px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
    }

    .schedule-card { border: 1px solid var(--line); border-radius: 10px; padding: 12px; margin: 10px 0; background: white; box-shadow: var(--shadow); }
    .schedule-terms { display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 8px; margin-top: 8px; }
    .term-summary { background: #f8fafc; border: 1px solid var(--line); border-radius: 8px; padding: 8px; font-size: 13px; }

    .toast {
      position: fixed;
      left: 50%;
      bottom: 18px;
      transform: translateX(-50%);
      background: #0f172a;
      color: white;
      padding: 10px 14px;
      border-radius: 8px;
      box-shadow: 0 12px 28px rgba(15,23,42,0.25);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.18s ease, transform 0.18s ease;
      z-index: 200;
      max-width: min(680px, calc(100vw - 24px));
      font-size: 13px;
    }

    .toast.visible { opacity: 1; transform: translateX(-50%) translateY(-4px); }

    @media (max-width: 1150px) {
      .builder-workspace, .settings-grid, .add-course-grid, .semester-control-row { grid-template-columns: 1fr; }
      .builder-workspace { padding-right: 0; }
      .required-side { position: static; width: auto; max-width: none; transform: none !important; }
      .required-toggle { display: none; }
      .required-bank { max-height: none; }
      .button-row button { width: 100%; }
    }

    @media (max-width: 900px) {
      .grid-2, .grid-3, .schedule-terms { grid-template-columns: 1fr; }
      .header-inner { align-items: flex-start; flex-direction: column; }
      nav { justify-content: flex-start; }
      .course-card { flex-basis: 260px; width: 260px; max-width: 260px; }
    }
  

    /* v9 cleaner layout overrides */
    main { max-width:none; width:100%; padding:18px 22px 40px; }
    .auth-shell { min-height:calc(100vh - 130px); display:flex; align-items:center; justify-content:center; }
    .auth-card { width:min(460px,96vw); background:#fff; border:1px solid #e5e7eb; border-radius:18px; padding:28px; box-shadow:0 14px 35px rgba(15,23,42,.08); }
    .auth-card h2 { margin:0 0 6px; font-size:28px; border:0; padding:0; }
    .auth-card .muted { font-size:14px; margin-bottom:18px; display:block; }
    .auth-card input,.auth-card button { height:44px; }
    .auth-footer { margin-top:16px; display:flex; gap:10px; flex-wrap:wrap; justify-content:center; }
    .auth-footer a { color:#2563eb; text-decoration:none; font-weight:700; }
    .builder-workspace { display:grid; grid-template-columns:minmax(0,1fr) 390px; gap:18px; align-items:start; }
    .required-side { position:sticky; top:14px; align-self:start; height:calc(100vh - 28px); overflow:auto; }
    .required-group-title { font-size:16px !important; font-weight:800; color:#0f172a; margin:12px 0 8px; }
    .required-group .course-card .detail { font-size:13px !important; }
    .term-grid { display:flex !important; flex-direction:column; gap:14px; }
    .term-box { width:100%; min-height:94px; display:flex; flex-wrap:wrap; align-items:flex-start; align-content:flex-start; gap:10px; padding:12px; border:1px solid #dbe4f0; border-radius:14px; background:#fff; }
    .term-title { width:100%; display:flex; align-items:center; justify-content:space-between; gap:10px; font-size:16px; border-bottom:1px solid #edf1f7; padding-bottom:8px; margin-bottom:2px; }
    .term-title-actions { display:flex; gap:6px; align-items:center; }
    .term-title-actions button { width:auto; padding:5px 9px; font-size:12px; }
    .course-card { width:275px; min-height:92px; display:grid; grid-template-columns:1fr; gap:8px; border-radius:12px; border:1px solid #d4dde9; background:#fff; box-shadow:0 3px 10px rgba(15,23,42,.06); cursor:grab; }
    .course-card .code { font-size:14px; font-weight:850; color:#111827; }
    .course-card .detail { font-size:12px; line-height:1.35; color:#475569; }
    .course-actions { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
    .course-actions button,.course-actions select { width:auto; }
    .comment-button { background:#64748b; }
    .section-button { background:#7c3aed; }
    .bottom-add-semester { margin-top:14px; display:flex; gap:10px; align-items:center; background:#fff; border:1px dashed #cbd5e1; border-radius:14px; padding:12px; }
    .bottom-add-semester select,.bottom-add-semester input { margin:0; }
    .bottom-add-semester button { width:auto; white-space:nowrap; }
    .modal-backdrop { position:fixed; inset:0; background:rgba(15,23,42,.45); display:none; align-items:center; justify-content:center; z-index:2000; padding:20px; }
    .modal-backdrop.visible { display:flex; }
    .modal { width:min(920px,96vw); max-height:88vh; overflow:auto; background:#fff; border-radius:18px; box-shadow:0 30px 80px rgba(0,0,0,.25); padding:22px; }
    .modal-header { display:flex; justify-content:space-between; align-items:center; gap:10px; border-bottom:1px solid #e5e7eb; padding-bottom:10px; margin-bottom:14px; }
    .section-list { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:10px; }
    .section-option { border:1px solid #dbe4f0; border-radius:12px; padding:10px; background:#fff; cursor:pointer; }
    .section-option:hover { border-color:#2563eb; background:#eff6ff; }
    .section-option.conflict { border-color:#ef4444; background:#fff1f2; cursor:not-allowed; opacity:.75; }
    .section-option.selected { border-color:#059669; background:#ecfdf5; }
    .section-meta { color:#475569; font-size:12px; margin-top:4px; }
    .hub-picker { border-top:1px solid #edf1f7; padding-top:6px; display:grid; gap:3px; }
    .hub-picker label { font-size:12px; display:flex; gap:5px; align-items:center; }
    @media (max-width:1000px){ .builder-workspace{grid-template-columns:1fr;} .required-side{position:relative;height:auto;} }


    /* v10 required panel + current-semester calendar builder */
    :root { --header-h: 72px; }
    .builder-workspace {
      grid-template-columns: minmax(0, 1fr) minmax(430px, 38vw) !important;
      gap: 18px !important;
      align-items: start !important;
    }
    .required-side {
      position: sticky !important;
      top: calc(var(--header-h) + 14px) !important;
      height: calc(100vh - var(--header-h) - 28px) !important;
      width: auto !important;
      max-width: none !important;
      overflow: visible !important;
      z-index: 20 !important;
    }
    .required-bank {
      height: 100% !important;
      max-height: none !important;
      overflow: auto !important;
      padding: 14px !important;
    }
    .required-side.collapsed { transform: translateX(calc(100% - 42px)) !important; }
    .required-toggle { top: 14px !important; }
    .required-group {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
      gap: 8px;
      align-items: start;
      margin-bottom: 14px;
    }
    .required-group-title {
      grid-column: 1 / -1;
      position: sticky;
      top: 0;
      background: rgba(255,255,255,.95);
      backdrop-filter: blur(6px);
      padding: 6px 0;
      z-index: 1;
    }
    .required-bank .course-card {
      width: 100% !important;
      max-width: none !important;
      min-height: 96px;
      margin: 0 !important;
    }
    .term-box {
      display: flex !important;
      flex-wrap: wrap !important;
      gap: 10px !important;
      align-content: flex-start !important;
    }
    .term-title { flex: 0 0 100% !important; }
    .course-card {
      flex: 0 0 245px !important;
      width: 245px !important;
      max-width: 245px !important;
    }
    .semester-page {
      display: grid;
      grid-template-columns: minmax(320px, 430px) minmax(0, 1fr);
      gap: 16px;
      align-items: start;
    }
    .semester-left {
      position: sticky;
      top: calc(var(--header-h) + 14px);
      max-height: calc(100vh - var(--header-h) - 28px);
      overflow: auto;
    }
    .section-search-list, .selected-section-list {
      display: grid;
      gap: 8px;
      max-height: 330px;
      overflow: auto;
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fff;
    }
    .section-chip {
      border: 1px solid #dbe4f0;
      border-radius: 12px;
      padding: 10px;
      background: #fff;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(15,23,42,.04);
    }
    .section-chip:hover { border-color: #2563eb; background: #eff6ff; }
    .section-chip.conflict { border-color: #ef4444; background: #fff1f2; cursor: not-allowed; opacity:.8; }
    .section-chip.selected { border-color:#059669; background:#ecfdf5; }
    .calendar-shell { background:#fff; border:1px solid var(--line); border-radius:16px; padding:14px; box-shadow:var(--shadow); overflow:auto; }
    .calendar-grid {
      position: relative;
      display: grid;
      grid-template-columns: 64px repeat(5, minmax(150px, 1fr));
      min-width: 900px;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      overflow: hidden;
      background: #fff;
    }
    .cal-head, .cal-time, .cal-cell {
      border-right: 1px solid #e5e7eb;
      border-bottom: 1px solid #e5e7eb;
      min-height: 42px;
      padding: 6px;
      font-size: 12px;
    }
    .cal-head { background:#f8fafc; font-weight:900; text-align:center; position:sticky; top:0; z-index:2; }
    .cal-time { background:#f8fafc; color:#64748b; font-weight:700; }
    .cal-cell { background:#fff; }
    .cal-event {
      border-radius: 10px;
      padding: 7px;
      font-size: 12px;
      background:#dbeafe;
      border:1px solid #93c5fd;
      color:#0f172a;
      overflow:hidden;
      box-shadow: 0 4px 12px rgba(15,23,42,.10);
    }
    .cal-event.preview { background:#fef3c7; border-color:#f59e0b; }
    .cal-event.conflict { background:#fee2e2; border-color:#ef4444; }
    .calendar-events-layer { position:absolute; inset:0; pointer-events:none; }
    .semester-controls-slim { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .semester-controls-slim button { width:auto; }
    @media (max-width: 1100px) {
      .builder-workspace, .semester-page { grid-template-columns: 1fr !important; }
      .required-side, .semester-left { position: static !important; height:auto !important; max-height:none !important; }
      .required-side.collapsed { transform:none !important; }
      .required-toggle { display:none !important; }
    }


    /* v11 edge-to-edge degree plan + cleaner Hub UI */
    main { max-width:none !important; width:100% !important; padding:10px 10px 36px !important; }
    .builder-page { width:100% !important; max-width:none !important; margin:0 !important; }
    .builder-top, .compact-section, .required-bank { border-radius:12px !important; }
    .builder-workspace { width:100% !important; grid-template-columns:minmax(0,1fr) minmax(420px,34vw) !important; }
    .schedule-side { min-width:0 !important; }
    .hub-check-panel { margin-top:10px; }
    .hub-check-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:8px; }
    .hub-option-panel { display:none; margin-top:10px; border:1px solid #dbe4f0; background:#f8fafc; border-radius:12px; padding:12px; }
    .hub-option-panel.visible { display:block; }
    .hub-tools-grid { display:grid; grid-template-columns:minmax(260px,1.2fr) minmax(260px,1fr); gap:12px; align-items:start; }
    .hub-results { max-height:260px; overflow:auto; border:1px solid #dbe4f0; background:white; border-radius:10px; }
    .hub-result { padding:9px; border-bottom:1px solid #eef2f7; cursor:pointer; }
    .hub-result:hover { background:#eff6ff; }
    .hub-chips { display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; }
    .hub-chip { font-size:11px; padding:3px 6px; border-radius:999px; border:1px solid #bfdbfe; background:#eff6ff; color:#1e3a8a; }
    .hub-picker.compact { border-top:1px solid #edf1f7; padding-top:6px; display:grid; gap:6px; }
    .hub-picker.compact .hub-summary { font-size:12px; color:#334155; line-height:1.25; }
    .hub-picker.compact button { width:auto; justify-self:start; }
    .course-actions .section-button { display:none !important; }
    @media (max-width:1100px){ .hub-tools-grid{grid-template-columns:1fr;} .builder-workspace{grid-template-columns:1fr !important;} }

</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="brand">
      <h1>BU Course Scheduler</h1>
      <div class="subtitle">Plan courses, compare student schedules, and track requirements.</div>
    </div>
    <nav>
      <span class="hello-pill" id="helloUser">Hello, guest</span>
      <a href="/build">Degree Plan</a>
      <a href="/semester">Current Semester</a>
      <a href="/schedules">View Schedules</a>
      <a href="/login" id="loginRegisterLink">Login / Register</a>
      <button id="navLogoutBtn" onclick="logoutFromNav()" style="display:none;">Logout</button>
    </nav>
  </div>
</header>

<main>
  {{ content|safe }}
</main>
<div id="toast" class="toast"></div>

<script>
const MAJOR_DATA = {{ major_data|safe }};
const TERM_LABELS = {{ term_labels|safe }};
const HUB_UNITS = [
  "Philosophical Inquiry & Life's Meanings (PLM)",
  "Aesthetic Exploration (AEX)",
  "Historical Consciousness (HCO)",
  "Social Inquiry (SO1 or SO2)",
  "Individual & Community (IIC)",
  "First Global Citizenship & Intercultural Literacy (GCI)",
  "Second Global Citizenship & Intercultural Literacy (GCI)",
  "Ethical Reasoning (ETR)"
];

let CURRENT_USER = null;
let toastTimer = null;

function showToast(message) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 3200);
}

function summarizeApiResult(status, data) {
  if (data && typeof data === "object") {
    if (data.message) return data.message;
    if (data.error) return data.error;
    if (data.user) return `Logged in as ${data.user.displayName || data.user.email}`;
    if (data.schedule) return "Schedule loaded.";
    if (Array.isArray(data)) return `Loaded ${data.length} item(s).`;
    if (typeof data.count === "number") return `Found ${data.count} result(s).`;
  }
  return status >= 200 && status < 300 ? "Request successful." : `Request failed (${status}).`;
}

function showResponse(data, boxId="responseBox") {
  // Kept for compatibility with older page scripts, but the UI no longer shows raw debug panels.
  if (data && typeof data === "object" && "status" in data) showToast(summarizeApiResult(data.status, data.data));
  else showToast(typeof data === "string" ? data : "Done.");
}

async function api(method, path, body=null) {
  const opts = { method, headers: {"Content-Type": "application/json"}, credentials: "same-origin" };
  if (body !== null) opts.body = JSON.stringify(body);
  const res = await fetch("/proxy" + path, opts);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  showToast(summarizeApiResult(res.status, data));
  await updateHeaderAuth();
  return {status: res.status, data};
}

async function updateHeaderAuth() {
  let user = null;
  try {
    const res = await fetch("/proxy/api/auth/me", {credentials:"same-origin"});
    const data = await res.json();
    user = data.user || null;
  } catch (err) {
    user = null;
  }

  CURRENT_USER = user;
  const hello = document.getElementById("helloUser");
  const link = document.getElementById("loginRegisterLink");
  const logout = document.getElementById("navLogoutBtn");

  if (user) {
    const name = user.displayName || user.email || "student";
    if (hello) hello.textContent = `Hello, ${name}`;
    if (link) link.style.display = "none";
    if (logout) logout.style.display = "inline-block";
  } else {
    if (hello) hello.textContent = "Hello, guest";
    if (link) link.style.display = "inline-block";
    if (logout) logout.style.display = "none";
  }
}

async function logoutFromNav() {
  await api("POST", "/api/auth/logout");
  await fetch("/clear-session", {method:"POST", credentials:"same-origin"});
  await updateHeaderAuth();
  showToast("Logged out.");
}

async function checkSession(show=false) {
  return updateHeaderAuth();
}

async function quickMe() {
  const result = await api("GET", "/api/auth/me");
  return result;
}

window.addEventListener("load", () => updateHeaderAuth());
</script>

{{ script|safe }}
</body>
</html>
"""

LOGIN_CONTENT = r"""
<div class="auth-shell"><section class="auth-card"><h2>Login</h2><span class="muted">Use your verified BU email to continue.</span><input id="loginEmail" placeholder="email@bu.edu"><input id="loginPassword" type="password" placeholder="password"><button onclick="loginUser()">Login</button><div class="auth-footer"><a href="/register">Create account</a><a href="/forgot">Forgot password?</a><a href="/verify">Verify email</a></div></section></div>
"""
REGISTER_CONTENT = r"""
<div class="auth-shell"><section class="auth-card"><h2>Register</h2><span class="muted">Create an account with a BU email.</span><input id="registerEmail" placeholder="email@bu.edu"><input id="registerPassword" type="password" placeholder="password"><input id="registerName" placeholder="display name"><button onclick="registerUser()">Register</button><div class="auth-footer"><a href="/login">Already have an account?</a><a href="/verify">Enter verification code</a></div></section></div>
"""
VERIFY_CONTENT = r"""
<div class="auth-shell"><section class="auth-card"><h2>Verify Email</h2><span class="muted">Enter the 6-digit code sent to your BU email.</span><input id="verifyEmail" placeholder="email@bu.edu"><input id="verifyCode" placeholder="6 digit code"><button onclick="verifyEmail()">Verify Email</button><button class="secondary" onclick="resendVerificationCode()">Resend Code</button><div class="auth-footer"><a href="/login">Back to login</a></div></section></div>
"""
FORGOT_CONTENT = r"""
<div class="auth-shell"><section class="auth-card"><h2>Forgot Password</h2><span class="muted">Send a reset code to your BU email.</span><input id="forgotEmail" placeholder="email@bu.edu"><button onclick="forgotPassword()">Send Reset Code</button><div class="auth-footer"><a href="/reset">I have a reset code</a><a href="/login">Back to login</a></div></section></div>
"""
RESET_CONTENT = r"""
<div class="auth-shell"><section class="auth-card"><h2>Reset Password</h2><span class="muted">Enter the code from your email and choose a new password.</span><input id="resetEmail" placeholder="email@bu.edu"><input id="resetCode" placeholder="6 digit reset code"><input id="newPassword" type="password" placeholder="new password"><button class="success" onclick="resetPassword()">Reset Password</button><div class="auth-footer"><a href="/forgot">Send a new code</a><a href="/login">Back to login</a></div></section></div>
"""
LOGIN_SCRIPT = r"""
<script>
function saveEmailFields(){["loginEmail","registerEmail","verifyEmail","forgotEmail","resetEmail"].forEach(id=>{const el=document.getElementById(id); if(el)localStorage.setItem(id,el.value||"");});}
function loadEmailFields(){["loginEmail","registerEmail","verifyEmail","forgotEmail","resetEmail"].forEach(id=>{const el=document.getElementById(id); if(!el)return; el.value=localStorage.getItem(id)||""; el.addEventListener("input",saveEmailFields);});}
async function registerUser(){const email=document.getElementById("registerEmail").value.trim(); const password=document.getElementById("registerPassword").value; const displayName=document.getElementById("registerName").value.trim(); localStorage.setItem("verifyEmail",email); localStorage.setItem("loginEmail",email); const r=await api("POST","/api/auth/register",{email,password,displayName}); if(r.status<400)setTimeout(()=>location.href="/verify",650);}
async function resendVerificationCode(){const email=(document.getElementById("verifyEmail")?.value||localStorage.getItem("verifyEmail")||"").trim(); await api("POST","/api/auth/resend-verification-code",{email});}
async function verifyEmail(){const r=await api("POST","/api/auth/verify-email",{email:document.getElementById("verifyEmail").value.trim(),code:document.getElementById("verifyCode").value.trim()}); if(r.status<400)setTimeout(()=>location.href="/login",650);}
async function loginUser(){saveEmailFields(); const r=await api("POST","/api/auth/login",{email:document.getElementById("loginEmail").value.trim(),password:document.getElementById("loginPassword").value}); if(r.status===200)setTimeout(()=>location.href="/build",500);}
async function forgotPassword(){const email=document.getElementById("forgotEmail").value.trim(); localStorage.setItem("resetEmail",email); const r=await api("POST","/api/auth/forgot-password",{email}); if(r.status<400)setTimeout(()=>location.href="/reset",650);}
async function resetPassword(){const r=await api("POST","/api/auth/reset-password",{email:document.getElementById("resetEmail").value.trim(),code:document.getElementById("resetCode").value.trim(),newPassword:document.getElementById("newPassword").value}); if(r.status<400)setTimeout(()=>location.href="/login",650);}
window.addEventListener("load",loadEmailFields);
</script>
"""

BUILD_CONTENT = r"""
<div class="builder-page">
  <section class="builder-top">
    <div>
      <h2>My Schedule Settings</h2>
      <div class="settings-grid">
        <input id="scheduleTitle" value="My Four-Year Plan" placeholder="Schedule title">
        <select id="scheduleMajor" multiple size="4" onchange="majorChanged()"></select>
      </div>
      <textarea id="scheduleComments" placeholder="Schedule notes">Built in the unified Flask schedule builder.</textarea>
      <div class="hub-check-panel">
        <h3>Unfulfilled Hub Units</h3>
        <p class="muted">This updates automatically from Hub units assigned on Hub Elective cards. Saved as <code>hub_unfulfilled</code>.</p>
        <div id="hubChecklist" class="hub-check-grid"></div>
      </div>
      <div class="button-row">
        <button class="success" onclick="saveSchedule()">Save/Update My Schedule</button>
        <button class="secondary" onclick="loadMySchedule()">Load My Existing Schedule</button>
        <button class="secondary" onclick="loadRequiredPlan()">Refresh Required List</button>
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
        <div id="hubOptionPanel" class="hub-option-panel">
          <h3>Hub Elective Helper</h3>
          <p class="muted">Pick a course from the Hub dataset, or manually choose the Hub units this placeholder will satisfy.</p>
          <div class="hub-tools-grid">
            <div>
              <label>Search Hub course data</label>
              <input id="hubCourseSearch" placeholder="Example: art, ethics, CASAH 225" oninput="searchHubCourseData()">
              <div id="hubCourseResults" class="hub-results"><div class="muted" style="padding:8px;">Start typing to search Hub courses.</div></div>
            </div>
            <div>
              <label>Manual Hub units for this Hub Elective</label>
              <div id="manualHubUnits" class="hub-check-grid"></div>
              <p class="muted">If you do not know the course yet, leave the card as “Hub Elective” and just select the units.</p>
            </div>
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
        <p class="muted">Drag cards into semesters or into Transferred Courses.</p>
        <div id="coursePalette" class="term-box palette-box" ondrop="dropCourse(event)" ondragover="allowDrop(event)"></div>
      </section>

      

      <section class="compact-section">
        <h2>My Schedule Builder</h2>
        <div id="termGrid" class="term-grid"></div>
        <div class="bottom-add-semester"><select id="newTermLabel"></select><input id="newTermCustom" placeholder="Custom semester label"><button onclick="addTermBox()">Add Semester</button></div>
      </section>

    </div>

    <aside class="required-side" id="requiredPanel">
      <button class="required-toggle" onclick="toggleRequiredPanel()">Hide</button>
      <section class="required-bank">
        <h2>Required Courses</h2>
        <p class="muted">Drag these into semesters. Already-placed requirements are hidden here.</p>
        <div id="requiredCourseBank"></div>
      </section>
    </aside>
  </div>
</div>
<div id="commentModal" class="modal-backdrop"><div class="modal"><div class="modal-header"><h2 id="commentModalTitle">Course Comments</h2><button class="secondary" onclick="closeModal('commentModal')">Close</button></div><textarea id="commentModalText" placeholder="Your comment for this course"></textarea><button onclick="saveModalComment()">Save Comment to This Card</button><h3>Other students' comments</h3><div id="otherStudentComments" class="scrollbox"></div></div></div>
<div id="hubModal" class="modal-backdrop"><div class="modal"><div class="modal-header"><h2>Choose Hub Course / Units</h2><button class="secondary" onclick="closeModal('hubModal')">Close</button></div><p class="muted">Search the Hub data object from the backend, select a course, or manually assign Hub units.</p><div class="hub-tools-grid"><div><label>Search Hub course</label><input id="modalHubSearch" placeholder="Example: CASAH 225, art, ethical" oninput="searchHubCourseData('modal')"><div id="modalHubResults" class="hub-results"></div></div><div><label>Manual Hub units</label><div id="modalHubUnits" class="hub-check-grid"></div><button onclick="saveHubModalUnits()">Save Hub Units</button></div></div></div></div>
"""

BUILD_SCRIPT = r"""
<script>
let nextCardId = 1;
let HUB_DATA_CACHE = null;
let ACTIVE_HUB_CARD = null;

function setupHubChecklist(selectedUnits=null) {
  const box = document.getElementById("hubChecklist");
  if (!box) return;
  const selected = new Set(selectedUnits || HUB_UNITS);
  box.innerHTML = HUB_UNITS.map(unit => `
    <label>
      <input type="checkbox" value="${escapeHtml(unit)}" ${selected.has(unit) ? "checked" : ""}>
      <span>${escapeHtml(unit)}</span>
    </label>
  `).join("");
}

function getUnfulfilledHubUnits() {
  const fulfilled = new Set();
  document.querySelectorAll(".course-card").forEach(card => {
    try { JSON.parse(card.dataset.hubUnits || "[]").forEach(u => fulfilled.add(u)); } catch {}
  });
  return HUB_UNITS.filter(u => !fulfilled.has(u));
}

function toggleRequiredPanel() {
  const panel = document.getElementById("requiredPanel");
  const btn = panel.querySelector(".required-toggle");
  panel.classList.toggle("collapsed");
  btn.textContent = panel.classList.contains("collapsed") ? "Show" : "Hide";
}

function setupBuilder() {
  // Restore local draft first if present, then users can choose to load saved backend plan.

  const majorSelect = document.getElementById("scheduleMajor");
  majorSelect.innerHTML = "";
  Object.keys(MAJOR_DATA).forEach((major, idx) => {
    const opt = document.createElement("option");
    opt.value = major;
    opt.textContent = major;
    if (idx === 0) opt.selected = true;
    majorSelect.appendChild(opt);
  });

  const newTerm = document.getElementById("newTermLabel");
  TERM_LABELS.forEach(t => {
    const opt = document.createElement("option");
    opt.value = t;
    opt.textContent = t;
    newTerm.appendChild(opt);
  });

  ensureTermBox("Transferred Courses", true);
  ["Freshman Fall","Freshman Spring","Sophomore Fall","Sophomore Spring","Junior Fall","Junior Spring","Senior Fall","Senior Spring"].forEach(t => ensureTermBox(t));
  setupHubChecklist();
  setupManualHubUnitControls("manualHubUnits");
  setupManualHubUnitControls("modalHubUnits");
  majorChanged();
  restoreLocalDegreeDraft();
  bindDegreeDraftAutosave();
}

function getSelectedMajors() {
  const sel = document.getElementById("scheduleMajor");
  return [...sel.selectedOptions].map(o => o.value).filter(Boolean);
}

function getPrimaryMajor() {
  return getSelectedMajors()[0] || Object.keys(MAJOR_DATA)[0];
}

function getCombinedDropdowns() {
  const combined = {};
  getSelectedMajors().forEach(major => {
    const d = MAJOR_DATA[major]?.dropdowns || {};
    Object.entries(d).forEach(([type, list]) => {
      combined[type] = combined[type] || [];
      list.forEach(item => { if (!combined[type].includes(item)) combined[type].push(item); });
    });
  });
  return combined;
}

function getCombinedRequiredPlan() {
  const combined = {};
  getSelectedMajors().forEach(major => {
    const plan = MAJOR_DATA[major]?.required_plan || {};
    Object.entries(plan).forEach(([term, courses]) => {
      combined[term] = combined[term] || [];
      courses.forEach(c => {
        if (!combined[term].some(x => x[0] === c[0])) combined[term].push(c);
      });
    });
  });
  return combined;
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
      transferred: card.dataset.transferred
    };
    const fresh = makeCourseCard(course);
    card.replaceWith(fresh);
  });
}

function updateRequirementDropdown() {
  const req = document.getElementById("requirementType");
  req.innerHTML = "";
  ["Regular Course", "Hub Elective"].concat(Object.keys(getCombinedDropdowns())).forEach(type => {
    if ([...req.options].some(o => o.value === type)) return;
    const opt = document.createElement("option");
    opt.value = type;
    opt.textContent = type;
    req.appendChild(opt);
  });
  requirementTypeChanged();
}

function requirementTypeChanged() {
  const type = document.getElementById("requirementType").value;
  const select = document.getElementById("electiveChoiceSelect");
  const hint = document.getElementById("electiveChoiceHint");
  const hubPanel = document.getElementById("hubOptionPanel");
  if (hubPanel) hubPanel.classList.toggle("visible", type === "Hub Elective");

  select.innerHTML = "";
  if (type === "Hub Elective") {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "Use Hub helper below or keep as generic Hub Elective";
    select.appendChild(opt);
    hint.textContent = "Use the Hub helper to choose a Hub course from backend Hub data or manually select Hub units.";
    return;
  }

  const options = getCombinedDropdowns()[type] || [];
  if (!options.length) {
    const opt = document.createElement("option"); opt.value=""; opt.textContent="No approved list for this type"; select.appendChild(opt);
    hint.textContent = "No program-sheet option list for this type. Use the manual course code box.";
    return;
  }
  const blank = document.createElement("option"); blank.value=""; blank.textContent=`Select ${type}...`; select.appendChild(blank);
  hint.textContent = `${options.length} approved option(s) loaded for ${type}. Select one from the dropdown.`;
  options.forEach(o => { const opt=document.createElement("option"); opt.value=o; opt.textContent=o; select.appendChild(opt); });
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
  box.innerHTML = `<div class="term-title"><span>${escapeHtml(termName)}</span><div class="term-title-actions"><button class="small secondary" onclick="moveTermBox(event, this, -1)">↑</button><button class="small secondary" onclick="moveTermBox(event, this, 1)">↓</button><button class="small danger" onclick="removeTermBox(event, this)">Remove</button></div></div>`;
  grid.appendChild(box);
}

function moveTermBox(event, button, dir) {
  event.stopPropagation();
  const box = button.closest(".term-box");
  if (!box) return;
  if (dir < 0 && box.previousElementSibling) box.parentNode.insertBefore(box, box.previousElementSibling);
  if (dir > 0 && box.nextElementSibling) box.parentNode.insertBefore(box.nextElementSibling, box);
}

function removeTermBox(event, button) {
  event.stopPropagation();
  const box = button.closest(".term-box");
  const term = box.dataset.term;
  if (term === "Transferred Courses") {
    alert("Transferred Courses cannot be removed.");
    return;
  }
  document.getElementById("coursePalette").append(...box.querySelectorAll(".course-card"));
  box.remove();
  loadRequiredPlan();
  saveLocalDegreeDraft();
}

function addTermBox() {
  const custom = document.getElementById("newTermCustom").value.trim();
  const label = custom || document.getElementById("newTermLabel").value;
  ensureTermBox(label);
  document.getElementById("newTermCustom").value = "";
  saveLocalDegreeDraft();
}

function loadRequiredPlan() {
  const plan = getCombinedRequiredPlan();
  const bank = document.getElementById("requiredCourseBank");
  if (!bank) return;

  // Count cards that are already placed in the user schedule. This prevents the
  // right-side required-course bank from repeatedly showing requirements that the
  // user has already dragged into a semester or Transferred Courses.
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
  if (type === "Hub Elective") return [];
  return getCombinedDropdowns()[type] || [];
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
  const isTransferred = course.transferred === true || course.transferred === "true" || (course.status || "").toLowerCase().includes("transferred");
  if (isTransferred) card.classList.add("completed");
  if ((course.course_code || "").includes("Elective")) card.classList.add("placeholder");

  card.id = "course-" + nextCardId++;
  card.draggable = true;
  card.ondragstart = dragCourse;
  card.dataset.code = course.course_code || "";
  card.dataset.comments = course.comments || "";
  card.dataset.requirementType = baseRequirementTypeFromCourse(course);
  card.dataset.selectedCourse = course.selected_course_code || "";
  card.dataset.sourceTerm = course.source_term || "";
  card.dataset.transferred = isTransferred ? "true" : "false";
  card.dataset.status = isTransferred ? "transferred" : (course.status || "planned");
  card.dataset.sections = JSON.stringify(course.selected_sections || []);
  card.dataset.hubUnits = JSON.stringify(course.hub_units || course.hub_areas || []);

  const choiceValue = course.comments || "";
  const choiceHtml = makeCardChoiceHtml(card.id, card.dataset.requirementType, choiceValue);
  const hubHtml = makeHubPickerHtml(card);

  card.innerHTML = `
    <div><div class="code">${escapeHtml(card.dataset.code)}</div><div class="detail">${escapeHtml(card.dataset.requirementType || "Course")}</div></div>
    <div class="detail"><span class="comment-text">${escapeHtml(card.dataset.comments)}</span><br>Status: <span class="status-text">${escapeHtml(card.dataset.status)}</span>${choiceHtml}${hubHtml}</div>
    <div class="course-actions">
      <label class="completed-toggle" onclick="event.stopPropagation()"><input type="checkbox" ${card.dataset.transferred === "true" ? "checked" : ""} onchange="toggleTransferred(event, this)"> Transferred</label>
      <button class="small comment-button" onclick="openCommentModal(event, this)">Comments</button>
      <button class="small success" onclick="markTransferred(event, this)">Transfer</button>
      <button class="small danger" onclick="removeCard(event, this)">Remove</button>
    </div>`;
  return card;
}

function makeHubPickerHtml(card) {
  const code = String(card.dataset.code || "");
  if (!code.includes("Hub Elective")) return "";
  let assigned = []; try { assigned = JSON.parse(card.dataset.hubUnits || "[]"); } catch {}
  const summary = assigned.length ? assigned.join(", ") : "No Hub units assigned yet";
  return `<div class="hub-picker compact"><span class="hub-summary">${escapeHtml(summary)}</span><button class="small secondary" onclick="openHubModal(event, this)">Choose Hub</button></div>`;
}

function setupManualHubUnitControls(containerId, selectedUnits=[]) {
  const box = document.getElementById(containerId);
  if (!box) return;
  const selected = new Set(selectedUnits || []);
  box.innerHTML = HUB_UNITS.map(unit => `<label><input type="checkbox" value="${escapeHtml(unit)}" ${selected.has(unit) ? "checked" : ""}> ${escapeHtml(unit)}</label>`).join("");
}

function getManualHubUnits(containerId) {
  const box = document.getElementById(containerId);
  if (!box) return [];
  return [...box.querySelectorAll("input:checked")].map(cb => cb.value);
}

async function getHubDataObject() {
  if (HUB_DATA_CACHE) return HUB_DATA_CACHE;
  const res = await api("GET", "/api/courses/hub");
  HUB_DATA_CACHE = res.data || {};
  return HUB_DATA_CACHE;
}

function hubCourseEntriesFromData(data) {
  return Object.entries(data || {}).map(([code, info]) => ({
    course_code: code,
    course_title: info?.name || "",
    hub_areas: info?.hub_areas || []
  }));
}

function hubCourseMatches(entry, query, missing=[]) {
  if (!entry.hub_areas || !entry.hub_areas.length) return false;
  const q = String(query || "").toLowerCase().trim();
  const text = `${entry.course_code} ${entry.course_title} ${entry.hub_areas.join(" ")}`.toLowerCase();
  if (q && !text.includes(q)) return false;
  if (missing.length && !entry.hub_areas.some(h => missing.includes(h))) return false;
  return true;
}

function renderHubCourseResults(container, entries, onPick) {
  if (!entries.length) {
    container.innerHTML = `<div class="muted" style="padding:8px;">No matching Hub courses found.</div>`;
    return;
  }
  container.innerHTML = entries.slice(0,80).map((c, idx) => `
    <div class="hub-result" data-idx="${idx}">
      <b>${escapeHtml(c.course_code)}</b> — ${escapeHtml(c.course_title)}
      <div class="hub-chips">${(c.hub_areas || []).map(h => `<span class="hub-chip">${escapeHtml(h)}</span>`).join("")}</div>
    </div>`).join("");
  [...container.querySelectorAll(".hub-result")].forEach(el => {
    el.onclick = () => onPick(entries[Number(el.dataset.idx)]);
  });
}

async function searchHubCourseData(mode="add") {
  const isModal = mode === "modal";
  const input = document.getElementById(isModal ? "modalHubSearch" : "hubCourseSearch");
  const container = document.getElementById(isModal ? "modalHubResults" : "hubCourseResults");
  if (!input || !container) return;
  container.innerHTML = `<div class="muted" style="padding:8px;">Searching Hub data...</div>`;
  const data = await getHubDataObject();
  const missing = getUnfulfilledHubUnits();
  const entries = hubCourseEntriesFromData(data)
    .filter(e => hubCourseMatches(e, input.value, missing.length ? missing : []))
    .sort((a,b) => (b.hub_areas.length - a.hub_areas.length) || a.course_code.localeCompare(b.course_code));
  renderHubCourseResults(container, entries, (course) => {
    if (isModal) applyHubCourseToActiveCard(course);
    else applyHubCourseToAddForm(course);
  });
}

function applyHubCourseToAddForm(course) {
  document.getElementById("manualCourseCode").value = `Hub Elective (${course.course_code})`;
  document.getElementById("manualCourseComment").value = course.course_title || "";
  setupManualHubUnitControls("manualHubUnits", course.hub_areas || []);
  showToast(`Selected ${course.course_code} for Hub Elective.`);
}

function openHubModal(event, button) {
  event.stopPropagation();
  ACTIVE_HUB_CARD = button.closest(".course-card");
  let units = []; try { units = JSON.parse(ACTIVE_HUB_CARD.dataset.hubUnits || "[]"); } catch {}
  setupManualHubUnitControls("modalHubUnits", units);
  const input = document.getElementById("modalHubSearch");
  if (input) input.value = "";
  document.getElementById("modalHubResults").innerHTML = `<div class="muted" style="padding:8px;">Search Hub courses or manually select units.</div>`;
  document.getElementById("hubModal").classList.add("visible");
}

function applyHubCourseToActiveCard(course) {
  if (!ACTIVE_HUB_CARD) return;
  ACTIVE_HUB_CARD.dataset.code = `Hub Elective (${course.course_code})`;
  ACTIVE_HUB_CARD.dataset.comments = course.course_title || "";
  ACTIVE_HUB_CARD.dataset.hubUnits = JSON.stringify(course.hub_areas || []);
  ACTIVE_HUB_CARD.querySelector(".code").textContent = ACTIVE_HUB_CARD.dataset.code;
  const commentEl = ACTIVE_HUB_CARD.querySelector(".comment-text");
  if (commentEl) commentEl.textContent = ACTIVE_HUB_CARD.dataset.comments;
  refreshHubSummary(ACTIVE_HUB_CARD);
  setupHubChecklist(getUnfulfilledHubUnits());
  saveLocalDegreeDraft();
  closeModal("hubModal");
}

function saveHubModalUnits() {
  if (!ACTIVE_HUB_CARD) return;
  const units = getManualHubUnits("modalHubUnits");
  ACTIVE_HUB_CARD.dataset.hubUnits = JSON.stringify(units);
  refreshHubSummary(ACTIVE_HUB_CARD);
  setupHubChecklist(getUnfulfilledHubUnits());
  saveLocalDegreeDraft();
  closeModal("hubModal");
}

function refreshHubSummary(card) {
  let units = []; try { units = JSON.parse(card.dataset.hubUnits || "[]"); } catch {}
  const summary = card.querySelector(".hub-summary");
  if (summary) summary.textContent = units.length ? units.join(", ") : "No Hub units assigned yet";
}

function hubCardChanged(event, checkbox) {
  event.stopPropagation();
  const card = checkbox.closest(".course-card");
  const units = [...card.querySelectorAll(".hub-picker input:checked")].map(cb => cb.value);
  card.dataset.hubUnits = JSON.stringify(units);
  refreshHubSummary(card);
  setupHubChecklist(getUnfulfilledHubUnits());
  saveLocalDegreeDraft();
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
    selected_course_code: selectedCode,
    hub_units: type === "Hub Elective" ? getManualHubUnits("manualHubUnits") : []
  }));

  document.getElementById("manualCourseCode").value = "";
  document.getElementById("manualCourseComment").value = "";
  setupManualHubUnitControls("manualHubUnits");
  document.getElementById("electiveChoiceSelect").value = "";
  saveLocalDegreeDraft();
}

function setCardTransferred(card, transferred) {
  card.dataset.transferred = transferred ? "true" : "false";
  card.dataset.status = transferred ? "transferred" : "planned";
  card.classList.toggle("completed", transferred);
  const detail = card.querySelector(".status-text");
  if (detail) detail.textContent = card.dataset.status;
}

function toggleTransferred(event, checkbox) {
  event.stopPropagation();
  const card = checkbox.closest(".course-card");
  setCardTransferred(card, checkbox.checked);
  loadRequiredPlan();
  saveLocalDegreeDraft();
}

function markTransferred(event, button) {
  event.stopPropagation();
  const card = button.closest(".course-card");
  setCardTransferred(card, true);
  const cb = card.querySelector(".completed-toggle input");
  if (cb) cb.checked = true;
  const transferredBox = document.querySelector(`.term-box[data-term="Transferred Courses"]`);
  transferredBox.appendChild(card);
  loadRequiredPlan();
}

function removeCard(event, button) {
  event.stopPropagation();
  button.closest(".course-card").remove();
  loadRequiredPlan();
  saveLocalDegreeDraft();
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
    saveLocalDegreeDraft();
  }
}

function buildScheduleJson() {
  const title = document.getElementById("scheduleTitle").value.trim();
  const majors = getSelectedMajors();
  const major = majors[0] || "";
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
        selected_sections: safeJson(card.dataset.sections, []),
        hub_units: safeJson(card.dataset.hubUnits, []),
        source_term: card.dataset.sourceTerm || "",
        status: card.dataset.status || "planned",
        transferred: card.dataset.transferred === "true"
      });
    });
  });

  return { title, major, majors, comments, hub_unfulfilled: getUnfulfilledHubUnits(), terms };
}


function saveLocalDegreeDraft() {
  try {
    if (!document.getElementById("termGrid")) return;
    localStorage.setItem("degreeScheduleDraft", JSON.stringify(buildScheduleJson()));
    localStorage.setItem("degreeScheduleDraftSavedAt", new Date().toISOString());
  } catch (err) { console.warn("Could not save local degree draft", err); }
}

function restoreLocalDegreeDraft() {
  try {
    const raw = localStorage.getItem("degreeScheduleDraft");
    if (!raw) return;
    const draft = JSON.parse(raw);
    if (!draft || !draft.terms) return;
    if (confirm("Restore your unsaved local degree-plan draft from this browser?")) {
      renderSchedule(draft);
      showToast("Restored local draft.");
    }
  } catch (err) { console.warn("Could not restore local degree draft", err); }
}

function bindDegreeDraftAutosave() {
  const root = document.querySelector(".builder-page");
  if (!root) return;
  root.addEventListener("input", () => setTimeout(saveLocalDegreeDraft, 80));
  root.addEventListener("change", () => setTimeout(saveLocalDegreeDraft, 80));
}

function previewSchedule() {
  navigator.clipboard?.writeText(JSON.stringify(buildScheduleJson(), null, 2));
  showToast("Schedule JSON copied to clipboard.");
}

async function saveSchedule() {
  const schedule = buildScheduleJson();
  if (!schedule.title) { alert("Title required."); return; }
  await api("POST", "/api/schedules", schedule);
  saveLocalDegreeDraft();
}

async function loadMySchedule() {
  const result = await api("GET", "/api/my-schedule");
  const schedule = result.data?.schedule || result.data?.data?.schedule;
  if (!schedule) { alert("No saved schedule found."); return; }
  renderSchedule(schedule);
}

function renderSchedule(schedule) {
  document.getElementById("scheduleTitle").value = schedule.title || "";
  const majorSelect = document.getElementById("scheduleMajor");
  const savedMajors = Array.isArray(schedule.majors) && schedule.majors.length ? schedule.majors : [schedule.major || Object.keys(MAJOR_DATA)[0]];
  [...majorSelect.options].forEach(opt => opt.selected = savedMajors.includes(opt.value));
  document.getElementById("scheduleComments").value = schedule.comments || "";
  updateRequirementDropdown();
  setupHubChecklist(schedule.hub_unfulfilled || HUB_UNITS);

  document.getElementById("termGrid").innerHTML = "";
  ensureTermBox("Transferred Courses", true);

  Object.entries(schedule.terms || {}).forEach(([term, courses]) => {
    if (term === "Required Courses") return;
    ensureTermBox(term, term === "Transferred Courses");
    const box = document.querySelector(`.term-box[data-term="${cssEscape(term)}"]`);
    courses.forEach(c => box.appendChild(makeCourseCard(c)));
  });
  loadRequiredPlan();
  saveLocalDegreeDraft();
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
      requirement_type: "Searched Course",
      hub_areas: course.hub?.hub_areas || []
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


function safeJson(value, fallback) { try { return JSON.parse(value || ""); } catch { return fallback; } }
let COMMENT_CARD = null; let SECTION_CARD = null;
function closeModal(id) { document.getElementById(id).classList.remove("visible"); }
async function openCommentModal(event, button) { event.stopPropagation(); COMMENT_CARD = button.closest(".course-card"); const code = COMMENT_CARD.dataset.code || ""; document.getElementById("commentModalTitle").textContent = `Comments for ${code}`; document.getElementById("commentModalText").value = COMMENT_CARD.dataset.comments || ""; document.getElementById("commentModal").classList.add("visible"); await loadOtherStudentComments(code); }
function saveModalComment() { if (!COMMENT_CARD) return; const text = document.getElementById("commentModalText").value.trim(); COMMENT_CARD.dataset.comments = text; const el = COMMENT_CARD.querySelector(".comment-text"); if (el) el.textContent = text; closeModal("commentModal"); showToast("Comment saved to card."); }
async function loadOtherStudentComments(code) { const box = document.getElementById("otherStudentComments"); box.innerHTML = `<div class="muted">Loading...</div>`; const result = await api("GET", "/api/schedules"); const schedules = Array.isArray(result.data) ? result.data : []; const key = requirementKeyFromCode(code); const comments = []; schedules.forEach(s => { Object.entries(s.terms || {}).forEach(([term, courses]) => { (courses || []).forEach(c => { if (requirementKeyFromCode(c.course_code || "") === key && c.comments) comments.push({ who: s.creator?.displayName || s.creator?.email || "Student", term, text: c.comments }); }); }); }); if (!comments.length) { box.innerHTML = `<div class="muted">No other comments found yet.</div>`; return; } box.innerHTML = comments.slice(0, 30).map(c => `<div class="section-option"><b>${escapeHtml(c.who)}</b> <span class="muted">${escapeHtml(c.term)}</span><br>${escapeHtml(c.text)}</div>`).join(""); }
async function openSectionPicker(event, button) { event.stopPropagation(); SECTION_CARD = button.closest(".course-card"); const code = extractActualCourseCode(SECTION_CARD.dataset.code || ""); document.getElementById("sectionModalTitle").textContent = `Sections for ${code}`; document.getElementById("sectionModal").classList.add("visible"); const list = document.getElementById("sectionList"); list.innerHTML = `<div class="muted">Loading sections...</div>`; if (!code || code.includes("Elective")) { list.innerHTML = `<div class="muted">Pick a concrete course code first.</div>`; return; } const result = await api("GET", "/api/courses/" + encodeURIComponent(code)); const sections = result.data?.sections || []; renderSectionOptions(sections); }
function extractActualCourseCode(code) { const paren = String(code).match(/\(([^)]+)\)/); return (paren ? paren[1] : code).trim(); }
function renderSectionOptions(sections) { const list = document.getElementById("sectionList"); if (!sections.length) { list.innerHTML = `<div class="muted">No sections found.</div>`; return; } const selected = safeJson(SECTION_CARD.dataset.sections, []); list.innerHTML = ""; sections.forEach(sec => { const div = document.createElement("div"); const selectedAlready = selected.some(s => s.class_nbr === sec.class_nbr); const conflict = !selectedAlready && selected.some(s => sectionsOverlap(s, sec)); div.className = "section-option" + (selectedAlready ? " selected" : "") + (conflict ? " conflict" : ""); div.title = conflict ? "Conflicts with a selected section." : "Click to select/unselect this section."; div.innerHTML = `<b>${escapeHtml(sec.display_title || sec.section_code_title || sec.section || "Section")}</b><div class="section-meta">${escapeHtml(sec.days || "")} ${escapeHtml(sec.start || "")} - ${escapeHtml(sec.end || "")}<br>${escapeHtml(sec.instructor || "")}<br>${escapeHtml(sec.status || "")}</div>`; div.onclick = () => { const current = safeJson(SECTION_CARD.dataset.sections, []); const exists = current.some(s => s.class_nbr === sec.class_nbr); if (exists) SECTION_CARD.dataset.sections = JSON.stringify(current.filter(s => s.class_nbr !== sec.class_nbr)); else { if (current.some(s => sectionsOverlap(s, sec))) { showToast("That section overlaps with another selected section for this course."); return; } current.push(sectionSlim(sec)); SECTION_CARD.dataset.sections = JSON.stringify(current); } renderSectionOptions(sections); }; list.appendChild(div); }); }
function sectionSlim(sec) { return { class_nbr: sec.class_nbr, section: sec.section, display_title: sec.display_title, section_code_title: sec.section_code_title, days: sec.days, start: sec.start, end: sec.end, instructor: sec.instructor, status: sec.status }; }
function sectionsOverlap(a,b) { const daysA=expandDays(a.days||""), daysB=expandDays(b.days||""); if (![...daysA].some(d=>daysB.has(d))) return false; const a1=timeToMin(a.start),a2=timeToMin(a.end),b1=timeToMin(b.start),b2=timeToMin(b.end); if ([a1,a2,b1,b2].some(x=>x===null)) return false; return a1 < b2 && b1 < a2; }
function expandDays(days) { const s=String(days||""); const out=new Set(); [["Mo","Mo"],["Tu","Tu"],["We","We"],["Th","Th"],["Fr","Fr"],["Sa","Sa"],["Su","Su"]].forEach(([t,v])=>{ if(s.includes(t)) out.add(v); }); return out; }
function timeToMin(t) { const m=String(t||"").trim().match(/^(\d{1,2}):(\d{2})\s*(am|pm)$/i); if(!m)return null; let h=Number(m[1]),min=Number(m[2]); const ap=m[3].toLowerCase(); if(ap==="pm"&&h!==12)h+=12; if(ap==="am"&&h===12)h=0; return h*60+min; }
async function suggestHubCoursesForCurrentTerm() { /* Hub suggestions now use the Hub Elective Helper and /api/courses/hub. */ }


window.addEventListener("load", setupBuilder);
</script>
"""


SEMESTER_CONTENT = r"""
<div class="semester-page">
  <section class="semester-left">
    <h2>Current Semester Builder</h2>
    <p class="muted">Search for a course, choose exact sections, and build a weekly calendar. This saves locally in your browser immediately, so reloads do not erase your work.</p>
    <div class="semester-controls-slim">
      <input id="semesterName" placeholder="Example: Fall 2026" value="Current Semester" oninput="saveSemesterDraft()">
      <button class="secondary" onclick="clearSemesterDraft()">Clear Local Draft</button>
    </div>
    <h3>Search course sections</h3>
    <input id="semesterCourseQuery" placeholder="Example: CAS PY 212 or software" onkeydown="if(event.key==='Enter') searchSemesterCourses()">
    <button onclick="searchSemesterCourses()">Search Sections</button>
    <div id="semesterSectionResults" class="section-search-list"><div class="muted">Search results will appear here.</div></div>
    <h3>Selected Sections</h3>
    <div id="selectedSections" class="selected-section-list"><div class="muted">No sections selected yet.</div></div>
    <h3>Hub Suggestions</h3>
    <p class="muted">Suggests 100–200 level Hub courses that satisfy multiple missing Hub units and do not conflict with your selected sections.</p>
    <button class="secondary" onclick="suggestSemesterHubCourses()">Suggest Hub Courses</button>
    <div id="semesterHubSuggestions" class="section-search-list"><div class="muted">Suggestions will appear here.</div></div>
  </section>
  <section class="calendar-shell">
    <h2>Weekly Calendar</h2>
    <div id="calendarGrid" class="calendar-grid"></div>
  </section>
</div>
"""

SEMESTER_SCRIPT = r"""
<script>
let SELECTED_SECTIONS = [];
let PREVIEW_SECTION = null;
const DAYS = ["Mo", "Tu", "We", "Th", "Fr"];
const START_HOUR = 8;
const END_HOUR = 22;

function semesterStorageKey() { return "currentSemesterSectionDraft"; }

function sectionUid(sec) {
  return [sec.course_code, sec.class_nbr, sec.section, sec.display_title].filter(Boolean).join("|");
}

function loadSemesterDraft() {
  try {
    const raw = localStorage.getItem(semesterStorageKey());
    if (!raw) return;
    const data = JSON.parse(raw);
    document.getElementById("semesterName").value = data.semesterName || "Current Semester";
    SELECTED_SECTIONS = Array.isArray(data.sections) ? data.sections : [];
  } catch (err) { console.warn(err); }
}

function saveSemesterDraft() {
  const data = {
    semesterName: document.getElementById("semesterName")?.value || "Current Semester",
    sections: SELECTED_SECTIONS,
    savedAt: new Date().toISOString()
  };
  localStorage.setItem(semesterStorageKey(), JSON.stringify(data));
}

function clearSemesterDraft() {
  if (!confirm("Clear locally saved current-semester draft?")) return;
  SELECTED_SECTIONS = [];
  PREVIEW_SECTION = null;
  localStorage.removeItem(semesterStorageKey());
  renderSelectedSections();
  renderCalendar();
  showToast("Local current-semester draft cleared.");
}

async function searchSemesterCourses() {
  const q = document.getElementById("semesterCourseQuery").value.trim();
  const box = document.getElementById("semesterSectionResults");
  if (!q) { box.innerHTML = `<div class="muted">Enter a course or keyword.</div>`; return; }
  box.innerHTML = `<div class="muted">Searching...</div>`;
  const exactCourseLike = /^[A-Za-z]{2,4}\s*[A-Za-z]{0,3}\s*\d{3}/.test(q);
  const res = exactCourseLike ? await api("GET", "/api/courses/" + encodeURIComponent(q)) : await api("GET", "/api/courses?q=" + encodeURIComponent(q));
  let sections = [];
  if (res.data?.sections) sections = res.data.sections;
  else if (res.data?.results) sections = res.data.results;
  renderSemesterSectionResults(sections || []);
}

function renderSemesterSectionResults(sections) {
  const box = document.getElementById("semesterSectionResults");
  if (!sections.length) { box.innerHTML = `<div class="muted">No matching sections.</div>`; return; }
  box.innerHTML = "";
  sections.slice(0, 250).forEach(sec => {
    const slim = slimSection(sec);
    const selected = SELECTED_SECTIONS.some(s => sectionUid(s) === sectionUid(slim));
    const conflict = !selected && SELECTED_SECTIONS.some(s => sectionsOverlap(s, slim));
    const div = document.createElement("div");
    div.className = "section-chip" + (selected ? " selected" : "") + (conflict ? " conflict" : "");
    div.innerHTML = `<b>${escapeHtml(slim.course_code || "")} — ${escapeHtml(slim.display_title || slim.section || "Section")}</b><div class="section-meta">${escapeHtml(slim.days || "")} ${escapeHtml(slim.start || "")} - ${escapeHtml(slim.end || "")}<br>${escapeHtml(slim.instructor || "")}<br>${escapeHtml(slim.status || "")}</div>`;
    div.onmouseenter = () => { PREVIEW_SECTION = slim; renderCalendar(); };
    div.onmouseleave = () => { PREVIEW_SECTION = null; renderCalendar(); };
    div.onclick = () => {
      if (selected) {
        SELECTED_SECTIONS = SELECTED_SECTIONS.filter(s => sectionUid(s) !== sectionUid(slim));
      } else {
        if (conflict) { showToast("That section conflicts with your current calendar."); return; }
        SELECTED_SECTIONS.push(slim);
      }
      saveSemesterDraft();
      renderSelectedSections();
      renderCalendar();
      renderSemesterSectionResults(sections);
    };
    box.appendChild(div);
  });
}

function slimSection(sec) {
  return {
    course_code: sec.course_code,
    course_title: sec.course_title,
    class_nbr: sec.class_nbr,
    section: sec.section,
    display_title: sec.display_title || sec.section_code_title,
    section_code_title: sec.section_code_title,
    days: sec.days,
    start: sec.start,
    end: sec.end,
    instructor: sec.instructor,
    status: sec.status,
    hub_areas: sec.hub?.hub_areas || sec.hub_areas || []
  };
}

function renderSelectedSections() {
  const box = document.getElementById("selectedSections");
  if (!SELECTED_SECTIONS.length) { box.innerHTML = `<div class="muted">No sections selected yet.</div>`; return; }
  box.innerHTML = "";
  SELECTED_SECTIONS.forEach(sec => {
    const div = document.createElement("div");
    div.className = "section-chip selected";
    div.innerHTML = `<b>${escapeHtml(sec.course_code || "")} — ${escapeHtml(sec.display_title || sec.section || "Section")}</b><div class="section-meta">${escapeHtml(sec.days || "")} ${escapeHtml(sec.start || "")} - ${escapeHtml(sec.end || "")}<br>${escapeHtml(sec.instructor || "")}</div><button class="small danger">Remove</button>`;
    div.querySelector("button").onclick = (e) => { e.stopPropagation(); SELECTED_SECTIONS = SELECTED_SECTIONS.filter(s => sectionUid(s) !== sectionUid(sec)); saveSemesterDraft(); renderSelectedSections(); renderCalendar(); };
    box.appendChild(div);
  });
}

function renderCalendar() {
  const grid = document.getElementById("calendarGrid");
  grid.innerHTML = "";
  grid.appendChild(cell("", "cal-head"));
  DAYS.forEach(d => grid.appendChild(cell(d, "cal-head")));
  for (let h = START_HOUR; h < END_HOUR; h++) {
    grid.appendChild(cell(formatHour(h), "cal-time"));
    DAYS.forEach(() => grid.appendChild(cell("", "cal-cell")));
  }
  const layer = document.createElement("div");
  layer.className = "calendar-events-layer";
  grid.appendChild(layer);
  SELECTED_SECTIONS.forEach(sec => drawSectionEvent(layer, sec, ""));
  if (PREVIEW_SECTION) drawSectionEvent(layer, PREVIEW_SECTION, SELECTED_SECTIONS.some(s => sectionsOverlap(s, PREVIEW_SECTION)) ? "conflict" : "preview");
}

function cell(text, cls) { const el=document.createElement("div"); el.className=cls; el.textContent=text; return el; }
function formatHour(h) { const ap = h >= 12 ? "PM" : "AM"; const hr = ((h + 11) % 12) + 1; return `${hr}:00 ${ap}`; }

function drawSectionEvent(layer, sec, extraClass) {
  const start = timeToMin(sec.start), end = timeToMin(sec.end);
  if (start == null || end == null || !sec.days) return;
  const rowHeight = 42;
  const headerHeight = 42;
  const col0 = 64;
  const gridWidth = document.getElementById("calendarGrid").clientWidth;
  const dayWidth = (gridWidth - col0) / 5;
  expandDays(sec.days).forEach(day => {
    const dayIndex = DAYS.indexOf(day);
    if (dayIndex < 0) return;
    const top = headerHeight + ((start - START_HOUR*60) / 60) * rowHeight;
    const height = Math.max(24, ((end - start) / 60) * rowHeight);
    const left = col0 + dayIndex * dayWidth + 4;
    const ev = document.createElement("div");
    ev.className = "cal-event " + (extraClass || "");
    ev.style.position = "absolute";
    ev.style.left = `${left}px`;
    ev.style.top = `${top}px`;
    ev.style.width = `${dayWidth - 8}px`;
    ev.style.height = `${height - 4}px`;
    ev.innerHTML = `<b>${escapeHtml(sec.course_code || "")}</b><br>${escapeHtml(sec.display_title || sec.section || "")}<br>${escapeHtml(sec.start || "")}–${escapeHtml(sec.end || "")}`;
    layer.appendChild(ev);
  });
}

function expandDays(days) { const s=String(days||""); const out=[]; [["Mo","Mo"],["Tu","Tu"],["We","We"],["Th","Th"],["Fr","Fr"]].forEach(([token,val])=>{ if(s.includes(token)) out.push(val); }); return out; }
function timeToMin(t) { const m=String(t||"").trim().match(/^(\d{1,2}):(\d{2})\s*(am|pm)$/i); if(!m)return null; let h=Number(m[1]),min=Number(m[2]); const ap=m[3].toLowerCase(); if(ap==="pm"&&h!==12)h+=12; if(ap==="am"&&h===12)h=0; return h*60+min; }
function sectionsOverlap(a,b) { const daysA=expandDays(a.days||""), daysB=expandDays(b.days||""); if (!daysA.some(d=>daysB.includes(d))) return false; const a1=timeToMin(a.start),a2=timeToMin(a.end),b1=timeToMin(b.start),b2=timeToMin(b.end); if([a1,a2,b1,b2].some(x=>x===null))return false; return a1 < b2 && b1 < a2; }

async function getHubDataObjectForSemester() {
  if (window.HUB_DATA_CACHE) return window.HUB_DATA_CACHE;
  const res = await api("GET", "/api/courses/hub");
  window.HUB_DATA_CACHE = res.data || {};
  return window.HUB_DATA_CACHE;
}
function hubEntriesForSemester(data) {
  return Object.entries(data || {}).map(([code, info]) => ({ course_code: code, course_title: info?.name || "", hub_areas: info?.hub_areas || [] }));
}
async function suggestSemesterHubCourses() {
  const box = document.getElementById("semesterHubSuggestions");
  box.innerHTML = `<div class="muted">Searching Hub data...</div>`;
  let missing = [];
  try { const draft = JSON.parse(localStorage.getItem("degreeScheduleDraft") || "{}"); missing = draft.hub_unfulfilled || []; } catch {}
  if (!missing.length) missing = HUB_UNITS;
  const data = await getHubDataObjectForSemester();
  const found = hubEntriesForSemester(data)
    .filter(c => (c.hub_areas || []).some(h => missing.includes(h)))
    .filter(c => {
      const num = Number((String(c.course_code).match(/(\d{3})/) || [])[1]);
      return num >= 100 && num <= 299 && (c.hub_areas || []).length >= 2;
    })
    .sort((a,b) => (b.hub_areas.length - a.hub_areas.length) || a.course_code.localeCompare(b.course_code));
  if (!found.length) { box.innerHTML = `<div class="muted">No 100–200 level multi-Hub suggestions found in Hub data.</div>`; return; }
  box.innerHTML = found.slice(0,24).map(c => `<div class="section-chip" onclick="loadSuggestedHubSections('${c.course_code.replace(/'/g,"\\'")}')"><b>${escapeHtml(c.course_code)}</b><div class="section-meta">${escapeHtml(c.course_title)}<br>${escapeHtml((c.hub_areas || []).join(", "))}<br><span class="muted">Click to load available sections.</span></div></div>`).join("");
}
async function loadSuggestedHubSections(code) {
  document.getElementById("semesterCourseQuery").value = code;
  await searchSemesterCourses();
}


function escapeHtml(str) { return String(str || "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;"); }
window.addEventListener("load", () => { loadSemesterDraft(); renderSelectedSections(); renderCalendar(); window.addEventListener("resize", renderCalendar); });
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
      <div class="muted">Student: ${escapeHtml(creator)} | Major: ${escapeHtml(s.major || "Unspecified")}</div>
      <p>${escapeHtml(s.comments || "")}</p>
      <div class="schedule-terms">${termHtml}</div>
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

@app.route("/register")
def register_page():
    return render_page(REGISTER_CONTENT, LOGIN_SCRIPT)

@app.route("/verify")
def verify_page():
    return render_page(VERIFY_CONTENT, LOGIN_SCRIPT)

@app.route("/forgot")
def forgot_page():
    return render_page(FORGOT_CONTENT, LOGIN_SCRIPT)

@app.route("/reset")
def reset_page():
    return render_page(RESET_CONTENT, LOGIN_SCRIPT)


@app.route("/build")
def build_page():
    return render_page(BUILD_CONTENT, BUILD_SCRIPT)



@app.route("/semester")
def semester_page():
    return render_page(SEMESTER_CONTENT, SEMESTER_SCRIPT)

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
