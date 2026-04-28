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

    .selected-course-group { border:1px solid var(--line); border-radius:14px; background:#fff; margin:10px 0; overflow:hidden; }
    .selected-course-group-header { padding:10px 12px; font-weight:800; background:#f8fafc; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; gap:10px; }
    .selected-course-group-body { padding:10px; display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:10px; }
    .degree-term-course-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:8px; }
    .tiny-pill { display:inline-flex; align-items:center; border-radius:999px; padding:2px 8px; background:#eef2ff; color:#3730a3; font-size:11px; font-weight:700; margin-right:4px; margin-top:4px; }
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



    /* v12 layout + Hub fixes */
    .builder-workspace {
      grid-template-columns: minmax(0, 1fr) clamp(340px, 30vw, 520px) !important;
      gap: 10px !important;
    }
    .required-side { padding-right: 0 !important; margin-right: 0 !important; }
    .required-bank { padding: 10px !important; margin-right: 0 !important; }
    .required-group {
      grid-template-columns: repeat(auto-fill, minmax(165px, 1fr)) !important;
      gap: 7px !important;
    }
    .required-bank .course-card { min-height: 82px !important; padding: 8px !important; }
    .required-bank .course-card .sublabel-text,
    .required-group .course-card .detail {
      font-size: 14px !important;
      line-height: 1.28 !important;
      color: #334155 !important;
    }
    .hub-track-item.done {
      border-color: #bbf7d0 !important;
      background: #f0fdf4 !important;
      color: #166534 !important;
    }
    .hub-track-item.missing {
      border-color: #fecaca !important;
      background: #fff7f7 !important;
      color: #991b1b !important;
    }
    .hub-track-item input:disabled { opacity: 1; accent-color: #16a34a; }
    @media (min-width: 1500px) {
      .builder-workspace { grid-template-columns: minmax(0, 1fr) clamp(420px, 34vw, 680px) !important; }
      .required-group { grid-template-columns: repeat(auto-fill, minmax(155px, 1fr)) !important; }
    }

    /* v14: remove right-side whitespace and make builder truly edge-to-edge */
    html, body { width: 100%; overflow-x: hidden; }
    main { max-width: none !important; width: 100% !important; padding-left: 10px !important; padding-right: 10px !important; box-sizing: border-box !important; }
    .builder-page { width: 100% !important; max-width: none !important; margin-left: 0 !important; margin-right: 0 !important; box-sizing: border-box !important; }
    .builder-workspace { width: 100% !important; max-width: none !important; padding-right: 0 !important; margin-right: 0 !important; box-sizing: border-box !important; display: grid !important; grid-template-columns: minmax(0, 1fr) minmax(500px, 34vw) !important; gap: 12px !important; align-items: start !important; }
    .schedule-side { width: 100% !important; min-width: 0 !important; box-sizing: border-box !important; }
    .required-side { width: 100% !important; max-width: none !important; min-width: 0 !important; margin: 0 !important; padding: 0 !important; justify-self: stretch !important; box-sizing: border-box !important; }
    .required-bank { width: 100% !important; max-width: none !important; margin: 0 !important; box-sizing: border-box !important; }
    .required-group { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)) !important; }
    @media (min-width: 1500px) { .builder-workspace { grid-template-columns: minmax(0, 1fr) minmax(560px, 32vw) !important; } .required-group { grid-template-columns: repeat(auto-fill, minmax(155px, 1fr)) !important; } }
    @media (max-width: 1100px) { .builder-workspace { grid-template-columns: 1fr !important; } .required-side { position: static !important; height: auto !important; } }

    /* v15: fixed sliding required-course panel that follows scroll without wasting right space */
    :root { --required-panel-w: clamp(430px, 31vw, 620px); }
    .builder-page { width: 100% !important; max-width: none !important; margin: 0 !important; box-sizing: border-box !important; }
    .builder-workspace { display: block !important; width: 100% !important; max-width: none !important; padding-right: calc(var(--required-panel-w) + 14px) !important; margin: 0 !important; box-sizing: border-box !important; }
    .schedule-side { width: 100% !important; max-width: none !important; min-width: 0 !important; box-sizing: border-box !important; }
    /* v16: keep required panel below the Add Course area instead of letting it float above it */
    :root { --required-top-offset: calc(var(--header-h) + 150px); }
    .required-side { position: fixed !important; top: var(--required-top-offset) !important; right: 8px !important; width: var(--required-panel-w) !important; max-width: calc(100vw - 58px) !important; height: calc(100vh - var(--required-top-offset) - 12px) !important; margin: 0 !important; padding: 0 !important; z-index: 30 !important; transition: transform 0.24s ease, box-shadow 0.24s ease !important; overflow: visible !important; }
    .required-side.collapsed { transform: translateX(calc(100% - 40px)) !important; }
    .required-toggle { display: block !important; position: absolute !important; left: -38px !important; top: 14px !important; width: 38px !important; min-width: 38px !important; height: 72px !important; border-radius: 10px 0 0 10px !important; padding: 0 !important; font-size: 11px !important; z-index: 31 !important; box-shadow: 0 8px 18px rgba(15,23,42,.13) !important; }
    .required-bank { width: 100% !important; height: 100% !important; max-height: none !important; overflow: auto !important; box-sizing: border-box !important; border-radius: 16px !important; box-shadow: 0 18px 45px rgba(15,23,42,.13) !important; }
    .required-group { display: grid !important; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)) !important; gap: 8px !important; align-items: start !important; }
    .required-bank .course-card { width: 100% !important; max-width: none !important; flex: none !important; }
    @media (min-width: 1500px) { :root { --required-panel-w: clamp(520px, 30vw, 720px); } .required-group { grid-template-columns: repeat(auto-fill, minmax(155px, 1fr)) !important; } }
    @media (max-width: 1100px) { .builder-workspace { display: block !important; padding-right: 0 !important; } .required-side { position: static !important; width: 100% !important; max-width: none !important; height: auto !important; transform: none !important; margin-top: 14px !important; } .required-toggle { display: none !important; } .required-bank { max-height: none !important; height: auto !important; } }



    /* v19 requested UI polish: compact settings, right utility rail, pastel contrast */
    :root{
      --pastel-blue:#eaf3ff;
      --pastel-green:#ecfdf3;
      --pastel-purple:#f3edff;
      --pastel-peach:#fff2e6;
      --pastel-pink:#fff0f6;
      --pastel-yellow:#fff9db;
      --right-rail-w: clamp(500px, 34vw, 720px);
    }
    .builder-page{padding:0 !important;}
    .builder-top{
      margin:0 0 10px 0 !important;
      padding:10px 12px !important;
      border-radius:14px !important;
      background:linear-gradient(135deg,#f8fbff,#f2fff8) !important;
    }
    .builder-top h2{font-size:18px !important;margin-bottom:6px !important;}
    .settings-grid{display:grid !important;grid-template-columns:minmax(240px, 1fr) minmax(300px, 1fr) !important;gap:10px !important;align-items:start !important;}
    #scheduleComments{min-height:44px !important;margin-top:8px !important;}
    #scheduleMajor{display:none !important;}
    .major-checkbox-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:6px;background:white;border:1px solid #dbe4f0;border-radius:12px;padding:8px;}
    .major-checkbox-grid label{display:flex;gap:6px;align-items:center;font-size:13px;font-weight:750;color:#334155;background:#f8fafc;border:1px solid #e5edf6;border-radius:10px;padding:7px 8px;}
    .major-checkbox-grid input{width:auto;margin:0;accent-color:#2563eb;}
    .hub-check-panel{margin-top:14px !important;background:#fff !important;border:1px solid #dbe4f0 !important;border-radius:14px !important;padding:12px !important;}
    .hub-check-panel h3{margin-top:0 !important;}
    .hub-check-panel.bottom-hub-tracker{margin:14px 0 0 0 !important;}
    .builder-workspace{display:block !important;padding-right:calc(var(--right-rail-w) + 12px) !important;}
    .schedule-side{width:100% !important;}
    .required-side{
      position:fixed !important;
      top:calc(var(--header-h) + 10px) !important;
      right:8px !important;
      width:var(--right-rail-w) !important;
      height:calc(100vh - var(--header-h) - 18px) !important;
      display:flex !important;
      flex-direction:column !important;
      gap:10px !important;
      z-index:35 !important;
      overflow:visible !important;
      transition:transform .24s ease !important;
    }
    .required-side.collapsed{transform:translateX(calc(100% - 42px)) !important;}
    .required-toggle{top:16px !important;}
    .right-tools{display:flex;flex-direction:column;gap:10px;min-height:0;}
    .right-tools .compact-section{margin:0 !important;border-radius:16px !important;background:#ffffff !important;}
    .right-tools .compact-section:nth-child(1){background:var(--pastel-blue) !important;border-color:#bfdbfe !important;}
    .right-tools .compact-section:nth-child(2){background:var(--pastel-purple) !important;border-color:#ddd6fe !important;}
    .right-tools .scrollbox{max-height:190px !important;}
    .required-bank{flex:1 1 auto !important;min-height:0 !important;overflow:auto !important;background:var(--pastel-green) !important;border-color:#bbf7d0 !important;border-radius:16px !important;}
    .required-group{grid-template-columns:repeat(auto-fill,minmax(145px,1fr)) !important;}
    .required-group-title{background:rgba(236,253,243,.96) !important;}
    .compact-section:has(#termGrid), .compact-section:has(.bottom-add-semester){background:#fff !important;border-radius:16px !important;}
    .term-box:nth-child(6n+1){background:#ffffff !important;border-color:#cfe3ff !important;}
    .term-box:nth-child(6n+2){background:#fffdf2 !important;border-color:#fde68a !important;}
    .term-box:nth-child(6n+3){background:#f8f3ff !important;border-color:#ddd6fe !important;}
    .term-box:nth-child(6n+4){background:#f0fdf4 !important;border-color:#bbf7d0 !important;}
    .term-box:nth-child(6n+5){background:#fff7ed !important;border-color:#fed7aa !important;}
    .term-box:nth-child(6n){background:#fdf2f8 !important;border-color:#fbcfe8 !important;}
    .course-card{background:#fff !important;border-color:#d7e0ee !important;box-shadow:0 4px 10px rgba(15,23,42,.06) !important;}
    .course-actions .completed-toggle,.course-actions button.success{display:none !important;}
    .bottom-add-semester{background:var(--pastel-yellow) !important;border-color:#fde68a !important;}
    .flash-open{animation:flashOpen .65s ease;}
    @keyframes flashOpen{0%{box-shadow:0 0 0 0 rgba(37,99,235,.55);transform:scale(.996);}55%{box-shadow:0 0 0 9px rgba(37,99,235,.08);}100%{box-shadow:none;transform:none;}}
    /* current semester page polish */
    .semester-left{background:#f8fbff !important;border:1px solid #dbeafe !important;border-radius:16px !important;padding:14px !important;}
    .calendar-shell{background:#fffdf7 !important;border-color:#fde68a !important;}
    #semesterName,#semesterScheduleTitle,#semesterScheduleComments{display:none !important;}
    #semesterHubSuggestions{max-height:none !important;overflow:visible !important;background:#fff !important;}
    .semester-left h3:nth-of-type(1){background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:8px;margin-top:14px;}
    .semester-left h3:nth-of-type(2){background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:8px;margin-top:14px;}
    .semester-left .section-search-list{border-radius:14px !important;}
    .cal-event{border-radius:10px !important;border-width:1px !important;}
    @media(max-width:1100px){.builder-workspace{padding-right:0 !important}.required-side{position:static !important;width:100% !important;height:auto !important;transform:none !important}.right-tools{display:block}.required-bank{max-height:none !important}.required-toggle{display:none !important}.settings-grid{grid-template-columns:1fr !important}}


    /* v20 polish: fixed card actions, right rail menu, color-coded planner */
    :root { --required-panel-w: clamp(520px, 34vw, 760px); --right-rail-w: var(--required-panel-w); }
    .course-card { position: relative !important; border-radius: 12px !important; box-shadow: 0 3px 9px rgba(15,23,42,.07) !important; border-width: 1px !important; }
    .course-card .x-remove { position:absolute; top:6px; right:6px; width:22px; height:22px; min-width:22px; padding:0; border-radius:999px; display:grid; place-items:center; font-size:14px; line-height:1; background:#fee2e2; color:#991b1b; border:1px solid #fecaca; }
    .course-card .x-remove:hover { background:#fecaca; }
    .course-card .code { padding-right: 26px; }
    .course-actions { margin-top: 8px; display:flex; align-items:center; gap:6px; justify-content:flex-start; }
    .comment-icon-button { width:auto !important; min-width:36px; padding:4px 8px !important; border-radius:999px !important; background:#eef2ff !important; color:#3730a3 !important; border:1px solid #c7d2fe !important; font-size:12px !important; }
    .comment-icon-button:hover { background:#e0e7ff !important; }
    .comment-count { font-weight:800; }
    .course-card.type-hub { background:#fff7ed !important; border-color:#fed7aa !important; }
    .course-card.type-core { background:#eef2ff !important; border-color:#c7d2fe !important; }
    .course-card.type-tech { background:#ecfdf5 !important; border-color:#bbf7d0 !important; }
    .course-card.type-writing { background:#fdf2f8 !important; border-color:#fbcfe8 !important; }
    .course-card.type-general { background:#f8fafc !important; border-color:#dbe4f0 !important; }
    .course-card.type-required { background:#eff6ff !important; border-color:#bfdbfe !important; }
    .course-card .detail { color:#475569; }
    .course-card .status-text, .completed-toggle { display:none !important; }
    .card-choice-wrap { margin-top:6px; }
    .term-box { background:#f8fafc !important; }
    .term-box[data-term*="Freshman Fall"], .term-box[data-term*="Senior Fall"] { background:#fef9c3 !important; border-color:#fde68a !important; }
    .term-box[data-term*="Freshman Spring"], .term-box[data-term*="Senior Spring"] { background:#e0f2fe !important; border-color:#bae6fd !important; }
    .term-box[data-term*="Sophomore"] { background:#f3e8ff !important; border-color:#e9d5ff !important; }
    .term-box[data-term*="Junior"] { background:#dcfce7 !important; border-color:#bbf7d0 !important; }
    .term-box[data-term="Transferred Courses"] { background:#fff1f2 !important; border-color:#fecdd3 !important; }
    .builder-top, .bottom-hub-tracker { width: calc(100% - var(--required-panel-w) - 20px) !important; max-width: none !important; box-sizing: border-box !important; }
    .builder-top .settings-grid { grid-template-columns: minmax(260px, 1fr) minmax(380px, 1.4fr) !important; }
    .bottom-hub-tracker { margin-top: 12px !important; }
    .required-side { top: calc(var(--header-h) + 12px) !important; height: calc(100vh - var(--header-h) - 24px) !important; }
    .required-bank { display:flex !important; flex-direction:column !important; overflow:hidden !important; padding:0 !important; }
    .required-scroll-menu { overflow:auto; padding:10px; height:100%; box-sizing:border-box; }
    .right-tools { display:block !important; }
    .right-menu-block { background:#fff; border:1px solid #e2e8f0; border-radius:14px; padding:10px; margin-bottom:10px; }
    .right-menu-block h2 { font-size:15px; margin:0 0 8px; border-bottom:0; padding:0; }
    .open-add-course-button { width:100%; background:#7c3aed !important; }
    #addCourseModal .modal { max-width: 980px; width:min(980px, 94vw); }
    #addCourseModal .compact-section { box-shadow:none !important; border:0 !important; padding:0 !important; margin:0 !important; background:transparent !important; }
    #addCourseModal .compact-section h2 { display:none; }
    .flash-target { animation: flashTarget 900ms ease-out; }
    @keyframes flashTarget { 0% { box-shadow:0 0 0 0 rgba(124,58,237,.35); transform:translateY(-2px); } 70% { box-shadow:0 0 0 12px rgba(124,58,237,0); } 100% { box-shadow:none; transform:none; } }
    #semesterScheduleComments { display:block !important; min-height:80px !important; margin-top:10px !important; }
    .semester-comment-box { margin-top:12px; padding:12px; border:1px solid #dbe4f0; border-radius:14px; background:#fff; }
    .cal-event { opacity:.92 !important; color:#0f172a !important; text-shadow:none !important; }
    .section-chip .section-meta { color:#475569 !important; }
    @media (max-width: 1100px) { .builder-top, .bottom-hub-tracker { width:100% !important; } }

  

    /* v21: always-on autosave + cleaner schedules page */
    .autosave-strip {
      display:flex; align-items:center; gap:8px;
      margin-top:8px; padding:8px 10px; border-radius:12px;
      background:#f0fdf4; border:1px solid #bbf7d0; color:#14532d;
      font-size:13px; font-weight:750;
    }
    .autosave-dot { width:9px; height:9px; border-radius:999px; background:#22c55e; display:inline-block; box-shadow:0 0 0 3px rgba(34,197,94,.12); }
    .autosave-strip.saving { background:#fffbeb; border-color:#fde68a; color:#92400e; }
    .autosave-strip.saving .autosave-dot { background:#f59e0b; box-shadow:0 0 0 3px rgba(245,158,11,.14); }
    .autosave-strip.saved { animation: autosavePulse .65s ease; }
    @keyframes autosavePulse { 0%{box-shadow:0 0 0 0 rgba(34,197,94,.35);} 100%{box-shadow:0 0 0 10px rgba(34,197,94,0);} }
    .major-picker-shell { background:#fff; border:1px solid #dbe4f0; border-radius:12px; padding:8px; }
    .settings-label { font-size:12px; font-weight:900; color:#334155; margin-bottom:6px; text-transform:uppercase; letter-spacing:.04em; }
    #majorCheckboxGrid.major-checkbox-grid { margin-top:0; border:0; padding:0; background:transparent; grid-template-columns:repeat(auto-fit,minmax(135px,1fr)); }
    .schedule-browser { display:grid; grid-template-columns:260px minmax(0,1fr); gap:14px; align-items:start; }
    .schedule-filter-panel { position:sticky; top:calc(var(--header-h) + 10px); background:#f8fafc; border:1px solid var(--line); border-radius:16px; padding:12px; box-shadow:var(--shadow); }
    .schedule-results-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(360px,1fr)); gap:12px; }
    .schedule-card.compact { margin:0; padding:12px; border-radius:16px; background:linear-gradient(135deg,#ffffff,#f8fbff); }
    .schedule-card.compact h3 { margin:0 0 4px; font-size:17px; }
    .schedule-meta-row { display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 8px; }
    .schedule-meta-pill { font-size:11px; font-weight:800; color:#334155; background:#eaf3ff; border:1px solid #bfdbfe; border-radius:999px; padding:3px 7px; }
    .schedule-year-block { margin-top:8px; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden; background:#fff; }
    .schedule-year-title { padding:7px 9px; font-weight:900; font-size:12px; color:#1e293b; background:#f1f5f9; border-bottom:1px solid #e2e8f0; }
    .schedule-term-mini { padding:7px 9px; border-bottom:1px solid #f1f5f9; }
    .schedule-term-mini:last-child { border-bottom:0; }
    .schedule-term-mini b { display:block; font-size:12px; color:#334155; margin-bottom:3px; }
    .mini-course-line { display:inline-block; font-size:11px; font-weight:750; color:#0f172a; background:#f8fafc; border:1px solid #e2e8f0; border-radius:999px; padding:2px 6px; margin:2px 3px 2px 0; }
    @media(max-width:900px){.schedule-browser{grid-template-columns:1fr}.schedule-filter-panel{position:static}.schedule-results-grid{grid-template-columns:1fr}}

  
    /* v24 polish */
    .autosave-strip { display: none !important; }
    .compact-degree-settings { grid-template-columns: 1fr !important; }
    #degreePlanTitle { font-size: 28px; margin-bottom: 8px; letter-spacing: -0.02em; }
    .right-menu-block.required-heading-v20 + h2,
    .right-menu-block.required-heading-v20 + h2 + p { display: none !important; }


    .last-save-v26 {
      margin-top: 8px;
      padding: 7px 8px;
      border-radius: 10px;
      background: #f8fafc;
      border: 1px solid #e5e7eb;
      font-size: 12px;
    }
    .schedule-tools-v26 .schedule-action-row-v25 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
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

async function api(method, path, body=null, options={}) {
  const opts = { method, headers: {"Content-Type": "application/json"}, credentials: "same-origin" };
  if (body !== null) opts.body = JSON.stringify(body);
  const res = await fetch("/proxy" + path, opts);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!options.silent) showToast(summarizeApiResult(res.status, data));
  if (!options.skipAuthRefresh) await updateHeaderAuth();
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
      <h2 id="degreePlanTitle">Degree Plan</h2>
      <div class="settings-grid compact-degree-settings">
        <input id="scheduleTitle" type="hidden" value="Degree Plan">
        <div class="major-picker-shell">
          <div class="settings-label">Majors</div>
          <select id="scheduleMajor" multiple size="4" onchange="majorChanged()"></select>
        </div>
      </div>
      <textarea id="scheduleComments" placeholder="Schedule notes">Built in the unified Flask schedule builder.</textarea>
      <div class="hub-check-panel">
        <h3>Hub Unit Tracker</h3>
        <p class="muted">Checked means fulfilled by assigned Hub Elective cards. Unchecked units are saved as <code>hub_unfulfilled</code>.</p>
        <div id="hubChecklist" class="hub-check-grid"></div>
      </div>
      <div class="autosave-strip" style="display:none;">
        <span class="autosave-dot" id="autosaveDot"></span>
        <span id="autosaveText"></span>
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

function setupHubChecklist(unfulfilledUnits=null) {
  const box = document.getElementById("hubChecklist");
  if (!box) return;
  // Checked = fulfilled. Unchecked = still missing and saved in hub_unfulfilled.
  const unfulfilled = new Set(Array.isArray(unfulfilledUnits) ? unfulfilledUnits : getUnfulfilledHubUnits());
  box.innerHTML = HUB_UNITS.map(unit => `
    <label class="hub-track-item ${unfulfilled.has(unit) ? "missing" : "done"}">
      <input type="checkbox" value="${escapeHtml(unit)}" ${unfulfilled.has(unit) ? "" : "checked"} disabled>
      <span>${escapeHtml(unit)}</span>
    </label>
  `).join("");
}

function getUnfulfilledHubUnits() {
  const fulfilledFamilies = new Set();
  document.querySelectorAll(".course-card").forEach(card => {
    try {
      JSON.parse(card.dataset.hubUnits || "[]").forEach(u => {
        const fam = hubFamily(u);
        if (fam) fulfilledFamilies.add(fam);
      });
    } catch {}
  });
  return HUB_UNITS.filter(unit => !fulfilledFamilies.has(hubFamily(unit)));
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
  bindDegreeDraftAutosave();
  autoLoadDegreeScheduleFromCacheOrServer();
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
        comments: "",
        requirement_type: inferType(code),
        source_term: term,
        sublabel: comment
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

function courseCardTypeClass(course, requirementType) {
  const code = String(course.course_code || "");
  const type = String(requirementType || code);
  if (code.includes("Hub Elective") || type.includes("Hub")) return "type-hub";
  if (type.includes("Core") || type.includes("Breadth") || type.includes("Fields") || type.includes("Professional") || type.includes("BME")) return "type-core";
  if (type.includes("Technical") || type.includes("Advanced") || type.includes("Engineering Elective") || type.includes("Computer Engineering Elective")) return "type-tech";
  if (code.includes("WR") || type.includes("Writing")) return "type-writing";
  if (type.includes("Required")) return "type-required";
  return "type-general";
}

function commentCountText(comments) {
  const n = String(comments || "").trim() ? 1 : 0;
  if (n <= 0) return "0";
  if (n > 9) return "9+";
  return String(n);
}

function makeCourseCard(course) {
  const card = document.createElement("div");
  card.className = "course-card";
  if ((course.course_code || "").includes("Elective")) card.classList.add("placeholder");

  card.id = "course-" + nextCardId++;
  card.draggable = true;
  card.ondragstart = dragCourse;
  card.dataset.code = course.course_code || "";
  card.dataset.comments = course.comments || "";
  card.dataset.requirementType = baseRequirementTypeFromCourse(course);
  card.dataset.selectedCourse = course.selected_course_code || "";
  card.dataset.sourceTerm = course.source_term || "";
  card.dataset.sublabel = course.sublabel || "";
  card.dataset.sections = JSON.stringify(course.selected_sections || []);
  card.dataset.hubUnits = JSON.stringify(course.hub_units || course.hub_areas || []);
  card.dataset.status = "planned";
  card.dataset.transferred = "false";
  card.classList.add(courseCardTypeClass(course, card.dataset.requirementType));

  const choiceValue = course.comments || "";
  const choiceHtml = makeCardChoiceHtml(card.id, card.dataset.requirementType, choiceValue);
  const hubHtml = makeHubPickerHtml(card);
  const cCount = commentCountText(card.dataset.comments);

  card.innerHTML = `
    <button class="x-remove" title="Remove course" onclick="removeCard(event, this)">×</button>
    <div class="course-main">
      <div class="code">${escapeHtml(card.dataset.code)}</div>
      <div class="detail sublabel-text">${escapeHtml(card.dataset.sublabel || card.dataset.requirementType || "Course")}</div>
      <div class="detail"><span class="comment-text">${escapeHtml(card.dataset.comments)}</span>${choiceHtml}${hubHtml}</div>
    </div>
    <div class="course-actions">
      <button class="small comment-icon-button" title="Comments" onclick="openCommentModal(event, this)">💬 <span class="comment-count">${cCount}</span></button>
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
  let data = res.data?.data || res.data || {};
  if (typeof data === "string") {
    try { data = JSON.parse(data); }
    catch {
      try { data = JSON.parse("{" + data.replace(/^\s*,?/, "").replace(/,?\s*$/, "") + "}"); }
      catch { data = {}; }
    }
  }
  HUB_DATA_CACHE = data || {};
  return HUB_DATA_CACHE;
}

function hubCourseEntriesFromData(data) {
  if (Array.isArray(data)) {
    return data.map(item => ({
      course_code: item.course_code || item.code || "",
      course_title: item.name || item.course_title || "",
      hub_areas: Array.isArray(item.hub_areas) ? item.hub_areas : []
    })).filter(x => x.course_code);
  }
  return Object.entries(data || {}).map(([code, info]) => ({
    course_code: code,
    course_title: info?.name || info?.course_title || "",
    hub_areas: Array.isArray(info?.hub_areas) ? info.hub_areas : []
  }));
}


function getDegreeDraftForSemesterPicker() {
  try { return JSON.parse(localStorage.getItem("degreeScheduleDraft") || "{}"); }
  catch { return {}; }
}

function refreshDegreeTermPicker() {
  const select = document.getElementById("degreeTermSelect");
  const picker = document.getElementById("degreeTermCoursePicker");
  if (!select || !picker) return;
  const draft = getDegreeDraftForSemesterPicker();
  const terms = draft.terms || {};
  const termNames = Object.keys(terms).filter(t => Array.isArray(terms[t]) && terms[t].length);
  if (!termNames.length) {
    select.innerHTML = `<option value="">No saved degree-plan semesters found</option>`;
    picker.innerHTML = `<div class="muted">Save or autosave your Degree Plan first, then refresh here.</div>`;
    return;
  }
  const previous = select.value;
  select.innerHTML = termNames.map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join("");
  if (previous && termNames.includes(previous)) select.value = previous;
  renderDegreeTermCourses();
}

function renderDegreeTermCourses() {
  const select = document.getElementById("degreeTermSelect");
  const picker = document.getElementById("degreeTermCoursePicker");
  if (!select || !picker) return;
  const term = select.value;
  const draft = getDegreeDraftForSemesterPicker();
  const courses = (draft.terms || {})[term] || [];
  if (!term || !courses.length) {
    picker.innerHTML = `<div class="muted">No courses in this semester.</div>`;
    return;
  }
  picker.innerHTML = `<div class="degree-term-course-grid">` + courses.map(c => {
    const code = extractActualCourseCode(c.selected_course_code || c.course_code || "");
    const label = c.course_code || code;
    const sub = c.comments || c.sublabel || c.requirement_type || "Click to search sections";
    return `<div class="section-chip" onclick="searchFromDegreeCourse('${escapeHtml(code).replaceAll("'", "\\'")}')"><b>${escapeHtml(label)}</b><div class="section-meta">${escapeHtml(sub)}</div></div>`;
  }).join("") + `</div>`;
}

async function searchFromDegreeCourse(code) {
  if (!code) return;
  document.getElementById("semesterCourseQuery").value = code;
  await searchSemesterCourses();
  document.getElementById("semesterSectionResults")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function sectionType(sec) {
  const text = `${sec.display_title || ""} ${sec.section_code_title || ""} ${sec.section || ""}`.toUpperCase();
  if (text.includes("LAB") || /^L\d/.test(String(sec.section || "").toUpperCase()) || /^M\d/.test(String(sec.section || "").toUpperCase())) return "LAB";
  if (text.includes("DIS") || text.includes("DISC") || /^D\d/.test(String(sec.section || "").toUpperCase()) || /^E\d/.test(String(sec.section || "").toUpperCase())) return "DIS";
  if (text.includes("LEC") || /^[ABC]\d/.test(String(sec.section || "").toUpperCase())) return "LEC";
  return "OTHER";
}

function sectionIsUsable(sec) {
  const status = String(sec.status || "").toLowerCase();
  return status.includes("open") && !status.includes("0 of") && sec.days && sec.start && sec.end;
}

function noInternalOverlap(bundle) {
  for (let i = 0; i < bundle.length; i++) {
    for (let j = i + 1; j < bundle.length; j++) {
      if (sectionsOverlap(bundle[i], bundle[j])) return false;
    }
  }
  return true;
}

function bundleFitsExisting(bundle) {
  return bundle.every(sec => !SELECTED_SECTIONS.some(existing => sectionsOverlap(existing, sec)));
}

function findCompatibleSectionBundle(sections) {
  const usable = (sections || []).map(slimSection).filter(sectionIsUsable);
  if (!usable.length) return null;
  const byType = { LEC: [], DIS: [], LAB: [], OTHER: [] };
  usable.forEach(sec => { byType[sectionType(sec)].push(sec); });

  const requiredTypes = [];
  if (byType.LEC.length) requiredTypes.push("LEC");
  if (byType.DIS.length) requiredTypes.push("DIS");
  if (byType.LAB.length) requiredTypes.push("LAB");
  if (!requiredTypes.length && byType.OTHER.length) requiredTypes.push("OTHER");

  function backtrack(idx, chosen) {
    if (idx === requiredTypes.length) {
      return noInternalOverlap(chosen) && bundleFitsExisting(chosen) ? chosen : null;
    }
    const type = requiredTypes[idx];
    for (const sec of byType[type].slice(0, 35)) {
      if (chosen.some(c => sectionsOverlap(c, sec))) continue;
      if (SELECTED_SECTIONS.some(existing => sectionsOverlap(existing, sec))) continue;
      const got = backtrack(idx + 1, [...chosen, sec]);
      if (got) return got;
    }
    return null;
  }

  return backtrack(0, []);
}

function matchedMissingHubAreas(entry, missing=[]) {
  const areas = entry.hub_areas || [];
  const matched = [];
  for (const req of missing || []) {
    if (areas.some(area => hubMatchesRequirement(area, req))) matched.push(req);
  }
  return matched;
}
function normalizeHubSearchText(text) {
  return String(text || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").replace(/\s+/g, " ").trim();
}

function hubFamily(text) {
  const t = normalizeHubSearchText(text);
  if (!t) return "";
  if (t.includes("philosophical")) return "PLM";
  if (t.includes("aesthetic")) return "AEX";
  if (t.includes("historical")) return "HCO";
  if (t.includes("social inquiry")) return "SO";
  if (t.includes("individual") && (t.includes("community") || t.includes("in community"))) return "IIC";
  if (t.includes("global citizenship") || t.includes("intercultural")) return "GCI";
  if (t.includes("ethical")) return "ETR";
  if (t.includes("writing intensive")) return "WIN";
  if (t.includes("research") && t.includes("information")) return "RIL";
  if (t.includes("digital") || t.includes("multimedia")) return "DME";
  if (t.includes("creativity") || t.includes("innovation")) return "CRI";
  if (t.includes("teamwork") || t.includes("collaboration")) return "TWC";
  if (t.includes("critical thinking")) return "CRT";
  if (t.includes("oral") || t.includes("signed")) return "OSC";
  return t;
}

function hubMatchesRequirement(hubArea, requirement) {
  const hf = hubFamily(hubArea);
  const rf = hubFamily(requirement);
  if (!hf || !rf) return false;
  return hf === rf;
}

function countMatchingMissingHubAreas(entry, missing=[]) {
  const areas = entry.hub_areas || [];
  const matched = new Set();
  for (const req of missing || []) {
    if (areas.some(area => hubMatchesRequirement(area, req))) matched.add(hubFamily(req));
  }
  return matched.size;
}

function hubCourseMatches(entry, query, missing=[]) {
  if (!entry.hub_areas || !entry.hub_areas.length) return false;
  const q = normalizeHubSearchText(query);
  const text = normalizeHubSearchText(`${entry.course_code} ${entry.course_title} ${entry.hub_areas.join(" ")}`);
  if (q) {
    const words = q.split(" ").filter(Boolean);
    if (!words.every(w => text.includes(w))) return false;
  }
  if (missing.length && countMatchingMissingHubAreas(entry, missing) === 0) return false;
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
  const palette = document.getElementById("coursePalette");
  if (palette) {
    palette.scrollIntoView({ behavior: "smooth", block: "center" });
    palette.classList.add("flash-target");
    setTimeout(() => palette.classList.remove("flash-target"), 1000);
  }
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
  const countEl = ACTIVE_HUB_CARD.querySelector(".comment-count");
  if (countEl) countEl.textContent = commentCountText(ACTIVE_HUB_CARD.dataset.comments);
  refreshHubSummary(ACTIVE_HUB_CARD);
  setupHubChecklist(getUnfulfilledHubUnits());
  saveLocalDegreeDraft();
  closeModal("hubModal");
  ACTIVE_HUB_CARD.scrollIntoView({ behavior: "smooth", block: "center" });
  ACTIVE_HUB_CARD.classList.add("flash-target");
  setTimeout(() => ACTIVE_HUB_CARD?.classList.remove("flash-target"), 1000);
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
        sublabel: card.dataset.sublabel || ""
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

function getLocalDegreeDraftMeta() {
  try {
    const raw = localStorage.getItem("degreeScheduleDraft");
    const savedAt = localStorage.getItem("degreeScheduleDraftSavedAt");
    const pulledAt = localStorage.getItem("degreeSchedulePulledAt");
    const serverUpdatedAt = localStorage.getItem("degreeScheduleServerUpdatedAt");
    const draft = raw ? JSON.parse(raw) : null;
    return { draft, savedAt, pulledAt, serverUpdatedAt };
  } catch (err) {
    console.warn("Could not read local degree draft metadata", err);
    return { draft: null, savedAt: null, pulledAt: null, serverUpdatedAt: null };
  }
}

function restoreLocalDegreeDraftSilently() {
  const { draft } = getLocalDegreeDraftMeta();
  if (draft && draft.terms) {
    renderSchedule(draft);
    showToast("Loaded local degree-plan draft.");
    return true;
  }
  return false;
}

function scheduleHasAnyCourses(schedule) {
  if (!schedule || !schedule.terms) return false;
  return Object.values(schedule.terms).some(list => Array.isArray(list) && list.length > 0);
}

function degreeDraftLooksBlank(schedule) {
  if (!schedule || !schedule.terms) return true;
  const hasCourses = scheduleHasAnyCourses(schedule);
  const hasTitle = !!String(schedule.title || "").trim();
  const hasComments = !!String(schedule.comments || "").trim();
  const hasMajor = !!(Array.isArray(schedule.majors) ? schedule.majors.length : schedule.major);
  return !hasCourses && !hasComments && !hasMajor && (!hasTitle || hasTitle === "My Degree Plan");
}

async function pullDegreeScheduleFromServer({force=false} = {}) {
  try {
    const result = await api("GET", "/api/my-schedule", null, { silent: true, skipAuthRefresh: true });
    const schedule = result.data?.schedule || result.data?.data?.schedule;

    if (!schedule) return null;

    localStorage.setItem("degreeScheduleDraft", JSON.stringify(schedule));
    localStorage.setItem("degreeScheduleDraftSavedAt", new Date().toISOString());
    localStorage.setItem("degreeSchedulePulledAt", new Date().toISOString());
    if (schedule.updatedAt) localStorage.setItem("degreeScheduleServerUpdatedAt", schedule.updatedAt);

    renderSchedule(schedule);
    showToast(force ? "Reloaded degree plan from server." : "Pulled latest degree plan from server.");
    return schedule;
  } catch (err) {
    console.warn("Could not pull degree schedule from server", err);
    return null;
  }
}

async function autoLoadDegreeScheduleFromCacheOrServer() {
  // v22 behavior: always try the server on page open when possible.
  // The old version could keep restoring a blank/outdated local draft and never show saved classes.
  await updateHeaderAuth();

  const meta = getLocalDegreeDraftMeta();
  const hasLocal = !!(meta.draft && meta.draft.terms);
  const localSavedAt = meta.savedAt ? Date.parse(meta.savedAt) : 0;
  const pulledAt = meta.pulledAt ? Date.parse(meta.pulledAt) : 0;
  const serverUpdatedAt = meta.serverUpdatedAt ? Date.parse(meta.serverUpdatedAt) : 0;

  // If the local draft is blank or only contains the default shell, do not let it block server loading.
  const localIsMeaningful = hasLocal && !degreeDraftLooksBlank(meta.draft);
  const localHasUnsyncedEdits = localIsMeaningful && localSavedAt > Math.max(pulledAt, serverUpdatedAt || 0);

  if (!localHasUnsyncedEdits) {
    const serverSchedule = await pullDegreeScheduleFromServer();
    if (serverSchedule) return;
  }

  // If server was unavailable and there is a meaningful local draft, use it.
  if (localIsMeaningful) {
    renderSchedule(meta.draft);
    showToast(localHasUnsyncedEdits ? "Restored unsynced local degree-plan draft." : "Loaded local degree-plan draft.");
    return;
  }

  // Last resort: save the default empty layout so localStorage exists.
  saveLocalDegreeDraft();
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
  const result = await api("POST", "/api/schedules", schedule);
  const saved = result.data?.schedule || result.data?.data?.schedule || result.data;
  if (saved && saved.terms) {
    localStorage.setItem("degreeScheduleDraft", JSON.stringify(saved));
    localStorage.setItem("degreeScheduleDraftSavedAt", new Date().toISOString());
    localStorage.setItem("degreeSchedulePulledAt", new Date().toISOString());
    if (saved.updatedAt) localStorage.setItem("degreeScheduleServerUpdatedAt", saved.updatedAt);
  } else {
    saveLocalDegreeDraft();
  }
}

async function loadMySchedule() {
  const schedule = await pullDegreeScheduleFromServer({force:true});
  if (!schedule) alert("No saved schedule found or you are not logged in.");
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
    (courses || []).forEach(c => box.appendChild(makeCourseCard(c)));
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




/* v19 behavior overrides */
const CANONICAL_TERM_ORDER = ["Freshman Fall","Freshman Spring","Freshman Summer","Sophomore Fall","Sophomore Spring","Sophomore Summer","Junior Fall","Junior Spring","Junior Summer","Senior Fall","Senior Spring","Senior Summer"];
function isCanonicalTermName(term){ return CANONICAL_TERM_ORDER.includes(term); }
function removeTransferredTermV19(){
  const box=document.querySelector('.term-box[data-term="Transferred Courses"]');
  if(!box)return;
  const pal=document.getElementById('coursePalette');
  if(pal) box.querySelectorAll('.course-card').forEach(c=>pal.appendChild(c));
  box.remove();
}
function sortTermBoxesV19(){
  const grid=document.getElementById('termGrid'); if(!grid)return;
  const boxes=[...grid.querySelectorAll('.term-box')];
  const canonical=boxes.filter(b=>isCanonicalTermName(b.dataset.term)).sort((a,b)=>CANONICAL_TERM_ORDER.indexOf(a.dataset.term)-CANONICAL_TERM_ORDER.indexOf(b.dataset.term));
  const custom=boxes.filter(b=>!isCanonicalTermName(b.dataset.term) && b.dataset.term!=="Transferred Courses");
  [...canonical,...custom].forEach(b=>grid.appendChild(b));
  decorateTermControlsV19();
}
function decorateTermControlsV19(){
  document.querySelectorAll('#termGrid .term-box').forEach(box=>{
    const canonical=isCanonicalTermName(box.dataset.term);
    box.querySelectorAll('.term-title-actions button').forEach(btn=>{
      if(btn.textContent.trim()==='↑'||btn.textContent.trim()==='↓') btn.style.display=canonical?'none':'';
    });
  });
}
function setupMajorCheckboxesV19(){
  const sel=document.getElementById('scheduleMajor'); if(!sel || document.getElementById('majorCheckboxGrid'))return;
  const grid=document.createElement('div'); grid.id='majorCheckboxGrid'; grid.className='major-checkbox-grid';
  [...sel.options].forEach(opt=>{
    const label=document.createElement('label');
    label.innerHTML=`<input type="checkbox" value="${escapeHtml(opt.value)}" ${opt.selected?'checked':''}> <span>${escapeHtml(opt.textContent)}</span>`;
    label.querySelector('input').addEventListener('change',()=>{ syncMajorSelectFromCheckboxesV19(); majorChanged(); saveLocalDegreeDraft(); });
    grid.appendChild(label);
  });
  sel.insertAdjacentElement('afterend', grid);
}
function syncMajorSelectFromCheckboxesV19(){
  const sel=document.getElementById('scheduleMajor'); const grid=document.getElementById('majorCheckboxGrid'); if(!sel||!grid)return;
  const checked=[...grid.querySelectorAll('input:checked')].map(i=>i.value);
  if(!checked.length){ const first=grid.querySelector('input'); if(first){ first.checked=true; checked.push(first.value); } }
  [...sel.options].forEach(o=>o.selected=checked.includes(o.value));
}
function syncMajorCheckboxesFromSelectV19(){
  const sel=document.getElementById('scheduleMajor'); const grid=document.getElementById('majorCheckboxGrid'); if(!sel||!grid)return;
  const selected=[...sel.selectedOptions].map(o=>o.value);
  grid.querySelectorAll('input').forEach(cb=>cb.checked=selected.includes(cb.value));
}
function restructureBuilderV19(){
  const panel=document.getElementById('requiredPanel'); if(!panel)return;
  if(!panel.querySelector('.right-tools')){
    const tools=document.createElement('div'); tools.className='right-tools';
    const sections=[...document.querySelectorAll('.schedule-side > section.compact-section')];
    const add=sections.find(sec=>sec.querySelector('h2')?.textContent.trim()==='Add Course');
    const palette=sections.find(sec=>sec.querySelector('h2')?.textContent.trim()==='Course Palette');
    if(add) tools.appendChild(add);
    if(palette) tools.appendChild(palette);
    panel.insertBefore(tools, panel.querySelector('.required-bank'));
  }
  const hub=document.querySelector('.hub-check-panel'); const page=document.querySelector('.builder-page');
  if(hub && page && !hub.classList.contains('bottom-hub-tracker')){ hub.classList.add('bottom-hub-tracker'); page.appendChild(hub); }
  removeTransferredTermV19(); sortTermBoxesV19();
}
function applyV19Ui(){ setupMajorCheckboxesV19(); restructureBuilderV19(); setupAutoBackendSaveV19(); }
const originalMoveTermBoxV19 = moveTermBox;
moveTermBox = function(event, button, dir){
  const box=button.closest('.term-box');
  if(box && isCanonicalTermName(box.dataset.term)){ event.stopPropagation(); showToast('Built-in year terms stay automatically sorted. Custom terms can be moved.'); return; }
  originalMoveTermBoxV19(event, button, dir); saveLocalDegreeDraft();
};
const originalAddTermBoxV19 = addTermBox;
addTermBox = function(){ originalAddTermBoxV19(); sortTermBoxesV19(); };
const originalEnsureTermBoxV19 = ensureTermBox;
ensureTermBox = function(termName, special=false){ if(termName==='Transferred Courses') return; originalEnsureTermBoxV19(termName, special); sortTermBoxesV19(); };
const originalRenderScheduleV19 = renderSchedule;
renderSchedule = function(schedule){ originalRenderScheduleV19(schedule); syncMajorCheckboxesFromSelectV19(); removeTransferredTermV19(); sortTermBoxesV19(); restructureBuilderV19(); };
const originalOpenHubModalV19 = openHubModal;
openHubModal = function(event, button){ originalOpenHubModalV19(event, button); setTimeout(()=>document.getElementById('hubModal')?.querySelector('.modal')?.classList.add('flash-open'),0); };
const originalSearchHubCourseDataV19 = searchHubCourseData;
searchHubCourseData = async function(mode='main'){ await originalSearchHubCourseDataV19(mode); const box=document.getElementById(mode==='modal'?'modalHubResults':'hubCourseResults'); if(box) box.classList.add('flash-open'); };
function setupAutoBackendSaveV19(){
  if(window.__autoBackendSaveV19)return; window.__autoBackendSaveV19=true;
  let timer=null;
  const root=document.querySelector('.builder-page'); if(!root)return;
  root.addEventListener('change',()=>{ clearTimeout(timer); timer=setTimeout(()=>{ saveLocalDegreeDraft(); queueServerAutosaveV20?.(); },180); });
  root.addEventListener('input',()=>{ clearTimeout(timer); timer=setTimeout(()=>{ saveLocalDegreeDraft(); queueServerAutosaveV20?.(); },260); });
}


/* v20 requested behavior overrides */
function ensureTermBoxV20(termName, special=false) {
  if (document.querySelector(`.term-box[data-term="${cssEscape(termName)}"]`)) return;
  const grid = document.getElementById("termGrid");
  if (!grid) return;
  const box = document.createElement("div");
  box.className = "term-box" + (special ? " special" : "");
  box.dataset.term = termName;
  box.ondragover = allowDrop;
  box.ondrop = dropCourse;
  const removable = termName !== "Transferred Courses";
  box.innerHTML = `<div class="term-title"><span>${escapeHtml(termName)}</span><div class="term-title-actions"><button class="small secondary" onclick="moveTermBox(event, this, -1)">↑</button><button class="small secondary" onclick="moveTermBox(event, this, 1)">↓</button>${removable ? `<button class="small danger" onclick="removeTermBox(event, this)">Remove</button>` : ""}</div></div>`;
  if (termName === "Transferred Courses") grid.insertBefore(box, grid.firstChild);
  else grid.appendChild(box);
}
ensureTermBox = ensureTermBoxV20;
removeTransferredTermV19 = function(){};

function ensureRequiredScrollMenuV20(){
  const bank=document.querySelector('.required-bank');
  if(!bank) return document.createElement('div');
  let menu=bank.querySelector('.required-scroll-menu');
  if(menu) return menu;
  menu=document.createElement('div');
  menu.className='required-scroll-menu';
  while(bank.firstChild) menu.appendChild(bank.firstChild);
  bank.appendChild(menu);
  return menu;
}
function setupAddCoursePopupV20(){
  const addSection=[...document.querySelectorAll('section.compact-section')].find(sec=>sec.querySelector('h2')?.textContent.trim()==='Add Course');
  const panel=document.getElementById('requiredPanel');
  if(!addSection || !panel || document.getElementById('addCourseModal')) return;
  const modal=document.createElement('div');
  modal.id='addCourseModal';
  modal.className='modal-backdrop add-course-modal';
  modal.innerHTML='<div class="modal"><div class="modal-header"><h2>Add Course</h2><button class="secondary" onclick="closeModal(\'addCourseModal\')">Close</button></div><div id="addCourseModalBody"></div></div>';
  document.body.appendChild(modal);
  modal.querySelector('#addCourseModalBody').appendChild(addSection);
  const btnBlock=document.createElement('div');
  btnBlock.className='right-menu-block add-course-launch';
  btnBlock.innerHTML='<h2>Add Course</h2><button class="open-add-course-button" onclick="openAddCourseModal()">+ Add Course</button><p class="muted">Add regular courses, Hub electives, or major-specific elective placeholders.</p>';
  const scrollMenu=ensureRequiredScrollMenuV20();
  scrollMenu.insertBefore(btnBlock, scrollMenu.firstChild);
}
function openAddCourseModal(){ document.getElementById('addCourseModal')?.classList.add('visible'); setTimeout(()=>document.getElementById('addCourseModal')?.querySelector('.modal')?.classList.add('flash-target'),0); }
const originalRestructureBuilderV20 = restructureBuilderV19;
restructureBuilderV19 = function(){
  originalRestructureBuilderV20();
  const panel=document.getElementById('requiredPanel');
  const menu=ensureRequiredScrollMenuV20();
  const rightTools=panel?.querySelector('.right-tools');
  const requiredCourseBank=document.getElementById('requiredCourseBank');
  if(rightTools && rightTools.parentElement !== menu) menu.insertBefore(rightTools, menu.firstChild);
  if(requiredCourseBank && requiredCourseBank.parentElement !== menu) menu.appendChild(requiredCourseBank);
  if(!menu.querySelector('.required-heading-v20')){
    const header=document.createElement('div'); header.className='right-menu-block required-heading-v20'; header.innerHTML='<h2>Required Courses</h2><p class="muted">Drag these into semesters. Already-placed requirements are hidden here.</p>';
    if(requiredCourseBank) menu.insertBefore(header, requiredCourseBank);
  }
  setupAddCoursePopupV20();
};
function classifyAllCourseCardsV20(){
  document.querySelectorAll('.course-card').forEach(card=>{
    ['type-hub','type-core','type-tech','type-writing','type-general','type-required'].forEach(c=>card.classList.remove(c));
    card.classList.add(courseCardTypeClass({course_code: card.dataset.code || ''}, card.dataset.requirementType || ''));
  });
}
const originalDropCourseV20=dropCourse;
dropCourse=function(event){ originalDropCourseV20(event); classifyAllCourseCardsV20(); queueServerAutosaveV20(); };
const originalRemoveCardV20=removeCard;
removeCard=function(event, button){ originalRemoveCardV20(event, button); queueServerAutosaveV20(); };
const originalCardChoiceChangedV20=cardChoiceChanged;
cardChoiceChanged=function(event,input){ originalCardChoiceChangedV20(event,input); classifyAllCourseCardsV20(); queueServerAutosaveV20(); };
const originalSaveHubModalUnitsV20=saveHubModalUnits;
saveHubModalUnits=function(){ originalSaveHubModalUnitsV20(); queueServerAutosaveV20(); };
let SERVER_AUTOSAVE_TIMER_V20=null;
async function silentSaveScheduleToServerV20(){
  if(!document.getElementById('termGrid')) return;
  const strip=document.getElementById('autosaveText');
  const wrap=document.querySelector('.autosave-strip');
  try{
    const schedule=buildScheduleJson();
    if(!schedule.title || !schedule.terms) return;
    if(strip) strip.textContent='Saving degree plan to server...';
    if(wrap){ wrap.classList.add('saving'); wrap.classList.remove('saved'); }
    const res=await fetch('/proxy/api/schedules',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify(schedule)});
    if(res.ok){
      localStorage.setItem('degreeSchedulePulledAt', new Date().toISOString());
      if(strip) strip.textContent='Saved to server and local browser cache.';
      if(wrap){ wrap.classList.remove('saving'); wrap.classList.add('saved'); setTimeout(()=>wrap.classList.remove('saved'),800); }
    } else if(res.status===401){
      if(strip) strip.textContent='Saved locally. Log in to sync to server.';
      if(wrap) wrap.classList.remove('saving');
    } else {
      if(strip) strip.textContent='Saved locally. Server sync will retry after changes.';
      if(wrap) wrap.classList.remove('saving');
    }
  }catch(err){
    console.warn('Background schedule save skipped', err);
    if(strip) strip.textContent='Saved locally. Server sync unavailable.';
    if(wrap) wrap.classList.remove('saving');
  }
}
function queueServerAutosaveV20(){ clearTimeout(SERVER_AUTOSAVE_TIMER_V20); SERVER_AUTOSAVE_TIMER_V20=setTimeout(silentSaveScheduleToServerV20, 650); }
const originalSaveLocalDegreeDraftV20 = saveLocalDegreeDraft;
saveLocalDegreeDraft = function(){ originalSaveLocalDegreeDraftV20(); queueServerAutosaveV20(); setupHubChecklist(getUnfulfilledHubUnits()); };
const originalAddManualCourseV20=addManualCourse;
addManualCourse=function(){ originalAddManualCourseV20(); closeModal('addCourseModal'); const pal=document.getElementById('coursePalette'); pal?.scrollIntoView({behavior:'smooth', block:'center'}); pal?.classList.add('flash-target'); setTimeout(()=>pal?.classList.remove('flash-target'),900); classifyAllCourseCardsV20(); queueServerAutosaveV20(); };
function moveSemesterCommentsBoxV20(){
  const textarea=document.getElementById('semesterScheduleComments');
  const hub=document.getElementById('semesterHubSuggestions');
  if(!textarea || !hub || textarea.closest('.semester-comment-box')) return;
  const wrap=document.createElement('div');
  wrap.className='semester-comment-box';
  wrap.innerHTML='<h3>Current semester notes</h3><p class="muted">Private local notes for this working semester schedule.</p>';
  hub.insertAdjacentElement('afterend', wrap);
  wrap.appendChild(textarea);
}
function pastelForCourseV20(code){
  const colors=[['#dbeafe','#93c5fd'],['#dcfce7','#86efac'],['#fef3c7','#fcd34d'],['#fce7f3','#f9a8d4'],['#ede9fe','#c4b5fd'],['#cffafe','#67e8f9'],['#ffedd5','#fdba74'],['#e0f2fe','#7dd3fc'],['#f5f3ff','#ddd6fe'],['#ecfccb','#bef264']];
  let h=0; String(code||'').split('').forEach(ch=>h=(h*31+ch.charCodeAt(0))>>>0);
  return colors[h%colors.length];
}
if (typeof drawSectionEvent === 'function') {
  const originalDrawSectionEventV20 = drawSectionEvent;
  drawSectionEvent = function(layer, sec, extraClass){
    const before = layer.children.length;
    originalDrawSectionEventV20(layer, sec, extraClass);
    for (let i = before; i < layer.children.length; i++) {
      const ev = layer.children[i];
      if (!extraClass) {
        const [bg, border] = pastelForCourseV20(sec.course_code);
        ev.style.background = bg;
        ev.style.borderColor = border;
      }
    }
  };
}
function applyV20Ui(){
  restructureBuilderV19();
  classifyAllCourseCardsV20();
  moveSemesterCommentsBoxV20();
  ensureTermBox('Transferred Courses', true);
  const grid=document.getElementById('termGrid'); const transfer=document.querySelector('.term-box[data-term="Transferred Courses"]'); if(grid&&transfer&&grid.firstChild!==transfer)grid.insertBefore(transfer, grid.firstChild);
}
window.addEventListener('load',()=>{ setTimeout(applyV20Ui, 100); setTimeout(applyV20Ui, 650); });

window.addEventListener("load", () => { setupBuilder(); applyV19Ui(); setTimeout(applyV19Ui, 250); });
window.addEventListener("load", () => { setTimeout(applyV20Ui, 400); });

/* v24 cleanup: no autosave, generated title, required heading de-dupe, hub suggestion close */
(function(){
  window.SERVER_AUTOSAVE_DISABLED_V24 = true;
  function currentUserDisplayNameV24() {
    const u = window.CURRENT_USER;
    if (!u) return "Student";
    const raw = u.displayName || u.email || "Student";
    return String(raw).split("@")[0] || "Student";
  }
  window.updateDegreePlanTitleV24 = function() {
    const name = currentUserDisplayNameV24();
    const title = `${name}'s Degree Plan`;
    const h = document.getElementById('degreePlanTitle');
    const input = document.getElementById('scheduleTitle');
    if (h) h.textContent = title;
    if (input) input.value = title;
    return title;
  };
  const oldUpdateHeaderAuthV24 = updateHeaderAuth;
  updateHeaderAuth = async function() {
    const result = await oldUpdateHeaderAuthV24();
    updateDegreePlanTitleV24();
    return result;
  };
  const oldBuildScheduleJsonV24 = buildScheduleJson;
  buildScheduleJson = function() {
    updateDegreePlanTitleV24();
    const schedule = oldBuildScheduleJsonV24();
    schedule.title = updateDegreePlanTitleV24();
    return schedule;
  };
  const oldRenderScheduleV24 = renderSchedule;
  renderSchedule = function(schedule) {
    oldRenderScheduleV24(schedule);
    updateDegreePlanTitleV24();
    dedupeRequiredHeadingsV24();
  };
  // Disable server autosave. Local draft caching remains active.
  queueServerAutosaveV20 = function() {};
  silentSaveScheduleToServerV20 = async function() {};
  const oldSaveLocalDegreeDraftV24 = saveLocalDegreeDraft;
  saveLocalDegreeDraft = function() {
    oldSaveLocalDegreeDraftV24();
    setupHubChecklist(getUnfulfilledHubUnits());
  };
  window.dedupeRequiredHeadingsV24 = function() {
    const panel = document.getElementById('requiredPanel');
    if (!panel) return;
    const menu = panel.querySelector('.required-scroll-menu') || panel;
    const headingBlocks = [...menu.querySelectorAll('.required-heading-v20')];
    headingBlocks.slice(1).forEach(h => h.remove());
    const h2s = [...menu.querySelectorAll('h2')].filter(h => h.textContent.trim() === 'Required Courses');
    h2s.forEach((h, idx) => {
      const owner = h.closest('.required-heading-v20');
      if (idx > 0 && !owner) {
        const p = h.nextElementSibling;
        if (p && p.classList.contains('muted')) p.remove();
        h.remove();
      }
    });
  };
  const oldRestructureBuilderV24 = restructureBuilderV19;
  restructureBuilderV19 = function() {
    oldRestructureBuilderV24();
    dedupeRequiredHeadingsV24();
    updateDegreePlanTitleV24();
  };
  const oldSuggestSemesterHubCoursesV24 = suggestSemesterHubCourses;
  suggestSemesterHubCourses = async function() {
    const box = document.getElementById('semesterHubSuggestions');
    if (box) { box.style.display = 'block'; box.classList.add('flash-target'); setTimeout(()=>box.classList.remove('flash-target'), 700); }
    return oldSuggestSemesterHubCoursesV24();
  };
  const oldLoadSuggestedHubSectionsV24 = loadSuggestedHubSections;
  loadSuggestedHubSections = async function(code) {
    const box = document.getElementById('semesterHubSuggestions');
    if (box) {
      box.classList.add('flash-target');
      box.innerHTML = `<div class="muted">Loaded ${escapeHtml(code)} into section search. Suggestions closed.</div>`;
    }
    await oldLoadSuggestedHubSectionsV24(code);
    if (box) setTimeout(() => { box.style.display = 'none'; box.classList.remove('flash-target'); }, 650);
    const list = document.getElementById('semesterSectionResults') || document.querySelector('.section-search-list');
    if (list) list.scrollIntoView({behavior:'smooth', block:'start'});
  };
  window.addEventListener('load', () => { updateDegreePlanTitleV24(); dedupeRequiredHeadingsV24(); });
})();


/* v25: put majors + save/load on right; fix generated title; de-dupe required headings */
(function(){
  function displayNameV25(){
    try {
      const u = (typeof CURRENT_USER !== 'undefined' && CURRENT_USER) ? CURRENT_USER : (window.CURRENT_USER || null);
      if (!u) return 'Student';
      const raw = u.displayName || u.email || 'Student';
      return String(raw).split('@')[0] || 'Student';
    } catch { return 'Student'; }
  }
  window.updateDegreePlanTitleV25 = function(){
    const title = `${displayNameV25()}'s Degree Plan`;
    const h = document.getElementById('degreePlanTitle');
    const input = document.getElementById('scheduleTitle');
    if (h) h.textContent = title;
    if (input) input.value = title;
    return title;
  };
  if (typeof updateDegreePlanTitleV24 === 'function') {
    updateDegreePlanTitleV24 = updateDegreePlanTitleV25;
  }
  function dedupeRequiredV25(){
    const panel = document.getElementById('requiredPanel');
    if (!panel) return;
    const menu = panel.querySelector('.required-scroll-menu') || panel;
    // Remove the original static heading that lives directly inside the required bank.
    panel.querySelectorAll('.required-bank > h2, .required-bank > p.muted').forEach(el => el.remove());
    // Keep only one generated Required Courses header.
    const blocks = [...menu.querySelectorAll('.required-heading-v20')];
    blocks.forEach((b, i) => { if (i > 0) b.remove(); });
    // If there are any stray Required Courses h2s not in the generated block, remove them.
    [...menu.querySelectorAll('h2')].forEach(h => {
      if (h.textContent.trim() === 'Required Courses' && !h.closest('.required-heading-v20')) {
        const p = h.nextElementSibling;
        if (p && p.classList.contains('muted')) p.remove();
        h.remove();
      }
    });
  }
  window.dedupeRequiredHeadingsV25 = dedupeRequiredV25;
  function ensureRightScheduleToolsV25(){
    const panel = document.getElementById('requiredPanel');
    if (!panel) return;
    const menu = (typeof ensureRequiredScrollMenuV20 === 'function') ? ensureRequiredScrollMenuV20() : (panel.querySelector('.required-scroll-menu') || panel);
    if (!menu) return;

    if (!document.getElementById('scheduleToolsV25')) {
      const tools = document.createElement('div');
      tools.id = 'scheduleToolsV25';
      tools.className = 'right-menu-block schedule-tools-v25';
      tools.innerHTML = `<h2>Schedule</h2><div class="schedule-action-row-v25"><button onclick="saveSchedule()">Save</button><button class="secondary" onclick="loadMySchedule()">Load</button></div>`;
      menu.insertBefore(tools, menu.firstChild);
    }

    const picker = document.querySelector('.major-picker-shell');
    if (picker && !picker.closest('.major-tools-v25')) {
      const block = document.getElementById('majorToolsV25') || document.createElement('div');
      block.id = 'majorToolsV25';
      block.className = 'right-menu-block major-tools-v25';
      if (!block.parentElement) {
        const after = document.getElementById('scheduleToolsV25');
        menu.insertBefore(block, after ? after.nextSibling : menu.firstChild);
      }
      if (!block.querySelector('h2')) block.appendChild(Object.assign(document.createElement('h2'), {textContent:'Majors'}));
      block.appendChild(picker);
    }
    // Make sure checkbox version of the major selector exists and is synced.
    if (typeof setupMajorCheckboxesV19 === 'function') setupMajorCheckboxesV19();
    if (typeof syncMajorCheckboxesFromSelectV19 === 'function') syncMajorCheckboxesFromSelectV19();
    dedupeRequiredV25();
  }
  window.ensureRightScheduleToolsV25 = ensureRightScheduleToolsV25;

  const oldUpdateHeaderV25 = updateHeaderAuth;
  updateHeaderAuth = async function(){
    const result = await oldUpdateHeaderV25();
    updateDegreePlanTitleV25();
    return result;
  };
  const oldBuildScheduleJsonV25 = buildScheduleJson;
  buildScheduleJson = function(){
    const schedule = oldBuildScheduleJsonV25();
    schedule.title = updateDegreePlanTitleV25();
    return schedule;
  };
  const oldRenderScheduleV25 = renderSchedule;
  renderSchedule = function(schedule){
    oldRenderScheduleV25(schedule);
    updateDegreePlanTitleV25();
    setTimeout(()=>{ ensureRightScheduleToolsV25(); dedupeRequiredV25(); }, 0);
  };
  if (typeof restructureBuilderV19 === 'function') {
    const oldRestructureV25 = restructureBuilderV19;
    restructureBuilderV19 = function(){
      oldRestructureV25();
      ensureRightScheduleToolsV25();
      dedupeRequiredV25();
      updateDegreePlanTitleV25();
    };
  }
  window.addEventListener('load', () => {
    setTimeout(async()=>{ await updateHeaderAuth(); ensureRightScheduleToolsV25(); dedupeRequiredV25(); updateDegreePlanTitleV25(); }, 150);
    setTimeout(()=>{ ensureRightScheduleToolsV25(); dedupeRequiredV25(); updateDegreePlanTitleV25(); }, 650);
  });
})();


/* v26: stronger title/user fix, right-side save/load timestamp, duplicate required cleanup */
(function(){
  function safeUserNameV26(){
    const candidates = [];
    try { if (typeof CURRENT_USER !== 'undefined' && CURRENT_USER) candidates.push(CURRENT_USER); } catch(e) {}
    try { if (window.CURRENT_USER) candidates.push(window.CURRENT_USER); } catch(e) {}
    try { const cached = JSON.parse(localStorage.getItem('lastKnownUser') || 'null'); if (cached) candidates.push(cached); } catch(e) {}
    const u = candidates.find(Boolean);
    if (!u) return 'Student';
    const raw = (u.displayName && String(u.displayName).trim()) || (u.email && String(u.email).trim()) || 'Student';
    const beforeAt = raw.split('@')[0];
    return beforeAt || 'Student';
  }

  function setDegreePlanTitleV26(){
    const name = safeUserNameV26();
    const title = `${name}'s Degree Plan`;
    const h = document.getElementById('degreePlanTitle');
    const input = document.getElementById('scheduleTitle');
    if (h) h.textContent = title;
    if (input) input.value = title;
    return title;
  }
  window.updateDegreePlanTitleV26 = setDegreePlanTitleV26;
  window.updateDegreePlanTitleV25 = setDegreePlanTitleV26;
  window.updateDegreePlanTitleV24 = setDegreePlanTitleV26;

  async function refreshUserForTitleV26(){
    try {
      const res = await fetch('/proxy/api/auth/me', {credentials:'same-origin'});
      const data = await res.json();
      const user = data.user || null;
      window.CURRENT_USER = user;
      if (user) localStorage.setItem('lastKnownUser', JSON.stringify(user));
      setDegreePlanTitleV26();
      return user;
    } catch(e) {
      setDegreePlanTitleV26();
      return null;
    }
  }

  if (typeof updateHeaderAuth === 'function') {
    const prevUpdateHeaderAuthV26 = updateHeaderAuth;
    updateHeaderAuth = async function(){
      const result = await prevUpdateHeaderAuthV26();
      await refreshUserForTitleV26();
      return result;
    };
  }

  function formatSaveTimeV26(iso){
    if (!iso) return 'Never saved in this browser session';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return 'Unknown';
    return d.toLocaleString([], {month:'short', day:'numeric', hour:'numeric', minute:'2-digit'});
  }

  function updateLastSaveLabelV26(){
    const el = document.getElementById('lastSaveTimestampV26');
    if (!el) return;
    const server = localStorage.getItem('degreeScheduleServerSaveAt') || localStorage.getItem('degreeScheduleServerUpdatedAt');
    const local = localStorage.getItem('degreeScheduleDraftSavedAt');
    el.textContent = `Last save: ${formatSaveTimeV26(server || local)}`;
  }
  window.updateLastSaveLabelV26 = updateLastSaveLabelV26;

  function cleanRequiredHeadingTextV26(){
    const panel = document.getElementById('requiredPanel');
    if (!panel) return;
    const menu = panel.querySelector('.required-scroll-menu') || panel;

    // Remove all direct/static Required Courses headings that are not the one generated in the scroll menu.
    [...panel.querySelectorAll('h2')].forEach(h => {
      if (h.textContent.trim() === 'Required Courses' && !h.closest('.required-heading-v20')) {
        const next = h.nextElementSibling;
        if (next && next.classList.contains('muted') && next.textContent.includes('Already-placed')) next.remove();
        h.remove();
      }
    });
    [...panel.querySelectorAll('p.muted')].forEach(p => {
      if (p.textContent.includes('Already-placed requirements are hidden here') && !p.closest('.required-heading-v20')) p.remove();
    });

    // Keep only one generated Required Courses block.
    const blocks = [...menu.querySelectorAll('.required-heading-v20')];
    blocks.forEach((b,i)=>{ if(i>0) b.remove(); });

    // If repeated plain text somehow remains, hide all but first identical pair by text content.
    const seen = new Set();
    [...menu.children].forEach(child => {
      const text = child.textContent.trim();
      if ((text === 'Required Courses' || text === 'Drag these into semesters. Already-placed requirements are hidden here.') && seen.has(text)) child.remove();
      seen.add(text);
    });
  }
  window.cleanRequiredHeadingTextV26 = cleanRequiredHeadingTextV26;

  function ensureRightPanelToolsV26(){
    const panel = document.getElementById('requiredPanel');
    if (!panel) return;
    const menu = (typeof ensureRequiredScrollMenuV20 === 'function') ? ensureRequiredScrollMenuV20() : (panel.querySelector('.required-scroll-menu') || panel);
    if (!menu) return;

    let tools = document.getElementById('scheduleToolsV25') || document.getElementById('scheduleToolsV26');
    if (!tools) {
      tools = document.createElement('div');
      tools.id = 'scheduleToolsV25';
      tools.className = 'right-menu-block schedule-tools-v25 schedule-tools-v26';
      menu.insertBefore(tools, menu.firstChild);
    }
    tools.innerHTML = `
      <h2>Schedule</h2>
      <div class="schedule-action-row-v25">
        <button onclick="saveSchedule()">Save</button>
        <button class="secondary" onclick="loadMySchedule()">Load from saved</button>
      </div>
      <div id="lastSaveTimestampV26" class="muted last-save-v26"></div>
    `;
    updateLastSaveLabelV26();

    let majorBlock = document.getElementById('majorToolsV25') || document.getElementById('majorToolsV26');
    const picker = document.querySelector('.major-picker-shell');
    if (picker) {
      if (!majorBlock) {
        majorBlock = document.createElement('div');
        majorBlock.id = 'majorToolsV25';
        majorBlock.className = 'right-menu-block major-tools-v25 major-tools-v26';
        tools.insertAdjacentElement('afterend', majorBlock);
      }
      if (!majorBlock.querySelector('h2')) {
        const h = document.createElement('h2');
        h.textContent = 'Majors';
        majorBlock.prepend(h);
      }
      if (!picker.closest('#majorToolsV25')) majorBlock.appendChild(picker);
    }
    if (typeof setupMajorCheckboxesV19 === 'function') setupMajorCheckboxesV19();
    if (typeof syncMajorCheckboxesFromSelectV19 === 'function') syncMajorCheckboxesFromSelectV19();
    cleanRequiredHeadingTextV26();
  }
  window.ensureRightPanelToolsV26 = ensureRightPanelToolsV26;
  window.ensureRightScheduleToolsV25 = ensureRightPanelToolsV26;

  if (typeof buildScheduleJson === 'function') {
    const prevBuildV26 = buildScheduleJson;
    buildScheduleJson = function(){
      const schedule = prevBuildV26();
      schedule.title = setDegreePlanTitleV26();
      return schedule;
    };
  }

  if (typeof saveLocalDegreeDraft === 'function') {
    const prevSaveLocalV26 = saveLocalDegreeDraft;
    saveLocalDegreeDraft = function(){
      prevSaveLocalV26();
      updateLastSaveLabelV26();
    };
  }

  if (typeof saveSchedule === 'function') {
    const prevSaveScheduleV26 = saveSchedule;
    saveSchedule = async function(){
      setDegreePlanTitleV26();
      const result = await prevSaveScheduleV26();
      const now = new Date().toISOString();
      localStorage.setItem('degreeScheduleServerSaveAt', now);
      localStorage.setItem('degreeScheduleDraftSavedAt', now);
      updateLastSaveLabelV26();
      return result;
    };
  }

  if (typeof loadMySchedule === 'function') {
    const prevLoadMyScheduleV26 = loadMySchedule;
    loadMySchedule = async function(){
      const result = await prevLoadMyScheduleV26();
      setDegreePlanTitleV26();
      updateLastSaveLabelV26();
      cleanRequiredHeadingTextV26();
      return result;
    };
  }

  if (typeof renderSchedule === 'function') {
    const prevRenderV26 = renderSchedule;
    renderSchedule = function(schedule){
      prevRenderV26(schedule);
      setDegreePlanTitleV26();
      setTimeout(()=>{ ensureRightPanelToolsV26(); cleanRequiredHeadingTextV26(); updateLastSaveLabelV26(); }, 0);
    };
  }

  if (typeof restructureBuilderV19 === 'function') {
    const prevRestructureV26 = restructureBuilderV19;
    restructureBuilderV19 = function(){
      prevRestructureV26();
      ensureRightPanelToolsV26();
      setDegreePlanTitleV26();
      cleanRequiredHeadingTextV26();
    };
  }

  // Make hub suggestion list close reliably after a selection.
  if (typeof loadSuggestedHubSections === 'function') {
    const prevLoadHubV26 = loadSuggestedHubSections;
    loadSuggestedHubSections = async function(code){
      const box = document.getElementById('semesterHubSuggestions');
      const result = await prevLoadHubV26(code);
      if (box) {
        box.innerHTML = '';
        box.style.display = 'none';
        box.classList.remove('flash-target');
      }
      return result;
    };
  }

  window.addEventListener('load', () => {
    refreshUserForTitleV26();
    setTimeout(()=>{ ensureRightPanelToolsV26(); setDegreePlanTitleV26(); cleanRequiredHeadingTextV26(); updateLastSaveLabelV26(); }, 200);
    setTimeout(()=>{ ensureRightPanelToolsV26(); setDegreePlanTitleV26(); cleanRequiredHeadingTextV26(); updateLastSaveLabelV26(); }, 900);
  });
})();

</script>
"""


SEMESTER_CONTENT = r"""
<div class="semester-page">
  <section class="semester-left">
    <h2>Current Semester Builder</h2>
    <p class="muted">Search for a course, choose exact sections, and build a weekly calendar. This saves locally in your browser immediately, so reloads do not erase your work.</p>
    <div class="semester-controls-slim">
      <input id="semesterName" placeholder="Example: Fall 2026" value="Current Semester" oninput="saveSemesterDraft()">
      <input id="semesterScheduleTitle" placeholder="Schedule title" value="Current Semester Schedule" oninput="saveSemesterDraft()">
      <button class="secondary" onclick="clearSemesterDraft()">Clear Local Draft</button>
    </div>
    <textarea id="semesterScheduleComments" placeholder="Schedule comments / notes" oninput="saveSemesterDraft()" style="min-height:64px; margin-top:8px;"></textarea>
    <h3>Search course sections</h3>
    <input id="semesterCourseQuery" placeholder="Example: CAS PY 212 or software" onkeydown="if(event.key==='Enter') searchSemesterCourses()">
    <button onclick="searchSemesterCourses()">Search Sections</button>
    <div id="semesterSectionResults" class="section-search-list"><div class="muted">Search results will appear here.</div></div>
    <h3>Hub Suggestions</h3>
    <p class="muted">Suggests 100–200 level Hub courses that satisfy multiple missing Hub units and do not conflict with your selected sections.</p>
    <button class="secondary" onclick="suggestSemesterHubCourses()">Suggest Hub Courses</button>
    <div id="semesterHubSuggestions" class="section-search-list"><div class="muted">Suggestions will appear here.</div></div>
  </section>
  <section class="calendar-shell">
    <h2>Weekly Calendar</h2>
    <div class="semester-controls-slim" style="margin-bottom:10px;">
      <select id="degreeTermSelect" onchange="renderDegreeTermCourses()"></select>
      <button class="secondary" onclick="refreshDegreeTermPicker()">Refresh Degree Plan Classes</button>
    </div>
    <div id="degreeTermCoursePicker" class="section-search-list" style="max-height:170px; margin-bottom:12px;">
      <div class="muted">Choose a semester from your degree plan to search its classes.</div>
    </div>
    <div id="calendarGrid" class="calendar-grid"></div>
    <h3 style="margin-top:18px;">Selected Sections</h3>
    <div id="selectedSections" class="selected-section-list"><div class="muted">No sections selected yet.</div></div>
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
    const titleEl = document.getElementById("semesterScheduleTitle");
    const commentsEl = document.getElementById("semesterScheduleComments");
    if (titleEl) titleEl.value = data.title || data.semesterTitle || "Current Semester Schedule";
    if (commentsEl) commentsEl.value = data.comments || data.semesterComments || "";
    SELECTED_SECTIONS = Array.isArray(data.sections) ? data.sections : [];
  } catch (err) { console.warn(err); }
}

function saveSemesterDraft() {
  const data = {
    semesterName: document.getElementById("semesterName")?.value || "Current Semester",
    title: document.getElementById("semesterScheduleTitle")?.value || "Current Semester Schedule",
    comments: document.getElementById("semesterScheduleComments")?.value || "",
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

function extractActualCourseCode(code) {
  const paren = String(code || "").match(/\(([^)]+)\)/);
  return (paren ? paren[1] : code || "").trim();
}

function normalizeCourseQueryForSearch(q) {
  return String(q || "").toUpperCase().replace(/[^A-Z0-9]+/g, " ").replace(/\s+/g, " ").trim();
}

function courseQueryVariants(q) {
  const base = normalizeCourseQueryForSearch(extractActualCourseCode(q));
  const variants = new Set([q, base]);
  const compactLetters = base.replace(/^([A-Z]+)\s+([A-Z]+)\s+(\d{3}[A-Z]?)$/, "$1$2 $3");
  variants.add(compactLetters);

  const m = base.match(/^([A-Z]{2,8})\s*(\d{3}[A-Z]?)$/);
  if (m) {
    variants.add(`${m[1]} ${m[2]}`);
    variants.add(`${m[1]}${m[2]}`);
    if (m[1].startsWith("CAS") && m[1].length > 3) variants.add(`CAS ${m[1].slice(3)} ${m[2]}`);
    if (m[1].startsWith("ENG") && m[1].length > 3) variants.add(`ENG ${m[1].slice(3)} ${m[2]}`);
  }

  const spaced = base.match(/^([A-Z]{2,4})\s+([A-Z]{1,4})\s+(\d{3}[A-Z]?)$/);
  if (spaced) {
    variants.add(`${spaced[1]}${spaced[2]} ${spaced[3]}`);
    variants.add(`${spaced[1]} ${spaced[2]} ${spaced[3]}`);
  }
  return [...variants].filter(Boolean);
}

async function fetchSectionsLenient(q) {
  const variants = courseQueryVariants(q);
  for (const v of variants) {
    const res = await api("GET", "/api/courses/" + encodeURIComponent(v), null, { silent: true, skipAuthRefresh: true });
    if (res.data?.sections?.length) return res.data.sections;
  }
  for (const v of variants) {
    const res = await api("GET", "/api/courses?q=" + encodeURIComponent(v), null, { silent: true, skipAuthRefresh: true });
    if (res.data?.results?.length) return res.data.results;
  }
  return [];
}

async function searchSemesterCourses() {
  const q = document.getElementById("semesterCourseQuery").value.trim();
  const box = document.getElementById("semesterSectionResults");
  if (!q) { box.innerHTML = `<div class="muted">Enter a course or keyword.</div>`; return; }
  box.innerHTML = `<div class="muted">Searching...</div>`;
  const sections = await fetchSectionsLenient(q);
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
  if (!box) return;
  if (!SELECTED_SECTIONS.length) {
    box.innerHTML = `<div class="muted">No sections selected yet.</div>`;
    return;
  }

  const groups = {};
  SELECTED_SECTIONS.forEach(sec => {
    const key = sec.course_code || "Other";
    if (!groups[key]) groups[key] = [];
    groups[key].push(sec);
  });

  box.innerHTML = Object.entries(groups).map(([courseCode, sections]) => {
    const courseTitle = sections.find(s => s.course_title)?.course_title || "";
    const body = sections.map(sec => `
      <div class="section-chip selected">
        <b>${escapeHtml(sec.display_title || sec.section || "Section")}</b>
        <div class="section-meta">
          ${escapeHtml(sec.days || "")} ${escapeHtml(sec.start || "")} - ${escapeHtml(sec.end || "")}<br>
          ${escapeHtml(sec.instructor || "")}
        </div>
        <button class="small danger" onclick="removeSelectedSection('${escapeHtml(sectionUid(sec)).replaceAll("'", "\\'")}')">Remove</button>
      </div>
    `).join("");
    return `
      <div class="selected-course-group">
        <div class="selected-course-group-header">
          <span>${escapeHtml(courseCode)}${courseTitle ? " — " + escapeHtml(courseTitle) : ""}</span>
          <span class="muted">${sections.length} selected</span>
        </div>
        <div class="selected-course-group-body">${body}</div>
      </div>
    `;
  }).join("");
}

function removeSelectedSection(uid) {
  SELECTED_SECTIONS = SELECTED_SECTIONS.filter(s => sectionUid(s) !== uid);
  saveSemesterDraft();
  renderSelectedSections();
  renderCalendar();
}

function renderCalendar() {
  const grid = document.getElementById("calendarGrid");
  if (!grid) return;
  if (grid.clientWidth === 0) { requestAnimationFrame(renderCalendar); return; }
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



function getDegreeDraftForSemesterPicker() {
  try { return JSON.parse(localStorage.getItem("degreeScheduleDraft") || "{}"); }
  catch { return {}; }
}

function refreshDegreeTermPicker() {
  const select = document.getElementById("degreeTermSelect");
  const picker = document.getElementById("degreeTermCoursePicker");
  if (!select || !picker) return;
  const draft = getDegreeDraftForSemesterPicker();
  const terms = draft.terms || {};
  const termNames = Object.keys(terms).filter(t => Array.isArray(terms[t]) && terms[t].length);
  if (!termNames.length) {
    select.innerHTML = `<option value="">No saved degree-plan semesters found</option>`;
    picker.innerHTML = `<div class="muted">Save or autosave your Degree Plan first, then refresh here.</div>`;
    return;
  }
  const previous = select.value;
  select.innerHTML = termNames.map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join("");
  if (previous && termNames.includes(previous)) select.value = previous;
  renderDegreeTermCourses();
}

function renderDegreeTermCourses() {
  const select = document.getElementById("degreeTermSelect");
  const picker = document.getElementById("degreeTermCoursePicker");
  if (!select || !picker) return;
  const term = select.value;
  const draft = getDegreeDraftForSemesterPicker();
  const courses = (draft.terms || {})[term] || [];
  if (!term || !courses.length) {
    picker.innerHTML = `<div class="muted">No courses in this semester.</div>`;
    return;
  }
  picker.innerHTML = `<div class="degree-term-course-grid">` + courses.map(c => {
    const code = extractActualCourseCode(c.selected_course_code || c.course_code || "");
    const label = c.course_code || code;
    const sub = c.comments || c.sublabel || c.requirement_type || "Click to search sections";
    return `<div class="section-chip" onclick="searchFromDegreeCourse('${escapeHtml(code).replaceAll("'", "\\'")}')"><b>${escapeHtml(label)}</b><div class="section-meta">${escapeHtml(sub)}</div></div>`;
  }).join("") + `</div>`;
}

async function searchFromDegreeCourse(code) {
  if (!code) return;
  document.getElementById("semesterCourseQuery").value = code;
  await searchSemesterCourses();
  document.getElementById("semesterSectionResults")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function sectionType(sec) {
  const text = `${sec.display_title || ""} ${sec.section_code_title || ""} ${sec.section || ""}`.toUpperCase();
  if (text.includes("LAB") || /^L\d/.test(String(sec.section || "").toUpperCase()) || /^M\d/.test(String(sec.section || "").toUpperCase())) return "LAB";
  if (text.includes("DIS") || text.includes("DISC") || /^D\d/.test(String(sec.section || "").toUpperCase()) || /^E\d/.test(String(sec.section || "").toUpperCase())) return "DIS";
  if (text.includes("LEC") || /^[ABC]\d/.test(String(sec.section || "").toUpperCase())) return "LEC";
  return "OTHER";
}

function sectionIsUsable(sec) {
  const status = String(sec.status || "").toLowerCase();
  return status.includes("open") && !status.includes("0 of") && sec.days && sec.start && sec.end;
}

function noInternalOverlap(bundle) {
  for (let i = 0; i < bundle.length; i++) {
    for (let j = i + 1; j < bundle.length; j++) {
      if (sectionsOverlap(bundle[i], bundle[j])) return false;
    }
  }
  return true;
}

function bundleFitsExisting(bundle) {
  return bundle.every(sec => !SELECTED_SECTIONS.some(existing => sectionsOverlap(existing, sec)));
}

function findCompatibleSectionBundle(sections) {
  const usable = (sections || []).map(slimSection).filter(sectionIsUsable);
  if (!usable.length) return null;
  const byType = { LEC: [], DIS: [], LAB: [], OTHER: [] };
  usable.forEach(sec => { byType[sectionType(sec)].push(sec); });

  const requiredTypes = [];
  if (byType.LEC.length) requiredTypes.push("LEC");
  if (byType.DIS.length) requiredTypes.push("DIS");
  if (byType.LAB.length) requiredTypes.push("LAB");
  if (!requiredTypes.length && byType.OTHER.length) requiredTypes.push("OTHER");

  function backtrack(idx, chosen) {
    if (idx === requiredTypes.length) {
      return noInternalOverlap(chosen) && bundleFitsExisting(chosen) ? chosen : null;
    }
    const type = requiredTypes[idx];
    for (const sec of byType[type].slice(0, 35)) {
      if (chosen.some(c => sectionsOverlap(c, sec))) continue;
      if (SELECTED_SECTIONS.some(existing => sectionsOverlap(existing, sec))) continue;
      const got = backtrack(idx + 1, [...chosen, sec]);
      if (got) return got;
    }
    return null;
  }

  return backtrack(0, []);
}

function matchedMissingHubAreas(entry, missing=[]) {
  const areas = entry.hub_areas || [];
  const matched = [];
  for (const req of missing || []) {
    if (areas.some(area => hubMatchesRequirement(area, req))) matched.push(req);
  }
  return matched;
}
function normalizeHubSearchText(text) {
  return String(text || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function hubFamily(text) {
  const t = normalizeHubSearchText(text);
  if (!t) return "";
  if (t.includes("philosophical")) return "PLM";
  if (t.includes("aesthetic")) return "AEX";
  if (t.includes("historical")) return "HCO";
  if (t.includes("social inquiry")) return "SO";
  if (t.includes("individual") && (t.includes("community") || t.includes("in community"))) return "IIC";
  if (t.includes("global citizenship") || t.includes("intercultural")) return "GCI";
  if (t.includes("ethical")) return "ETR";
  if (t.includes("writing intensive")) return "WIN";
  if (t.includes("research") && t.includes("information")) return "RIL";
  if (t.includes("digital") || t.includes("multimedia")) return "DME";
  if (t.includes("creativity") || t.includes("innovation")) return "CRI";
  if (t.includes("teamwork") || t.includes("collaboration")) return "TWC";
  if (t.includes("critical thinking")) return "CRT";
  if (t.includes("oral") || t.includes("signed")) return "OSC";
  return t;
}

function hubMatchesRequirement(hubArea, requirement) {
  const hf = hubFamily(hubArea);
  const rf = hubFamily(requirement);
  if (!hf || !rf) return false;
  return hf === rf;
}

function countMatchingMissingHubAreas(entry, missing=[]) {
  const areas = entry.hub_areas || [];
  const matched = new Set();
  for (const req of missing || []) {
    if (areas.some(area => hubMatchesRequirement(area, req))) matched.add(hubFamily(req));
  }
  return matched.size;
}

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
  box.innerHTML = `<div class="muted">Searching Hub data and checking section fit...</div>`;

  let missing = [];
  try {
    const draft = JSON.parse(localStorage.getItem("degreeScheduleDraft") || "{}");
    missing = draft.hub_unfulfilled || [];
  } catch {}
  if (!missing.length) missing = HUB_UNITS;

  const data = await getHubDataObjectForSemester();
  const candidates = hubEntriesForSemester(data)
    .map(c => ({
      ...c,
      filledHubUnits: matchedMissingHubAreas(c, missing),
      missingMatches: countMatchingMissingHubAreas(c, missing)
    }))
    .filter(c => {
      const num = Number((String(c.course_code).match(/(\d{3})/) || [])[1]);
      return num >= 100 && num <= 299 && c.missingMatches >= 2;
    })
    .sort((a,b) => (b.missingMatches - a.missingMatches) || (b.hub_areas.length - a.hub_areas.length) || a.course_code.localeCompare(b.course_code))
    .slice(0, 45);

  const fits = [];
  for (const c of candidates) {
    if (fits.length >= 18) break;
    try {
      const res = await api("GET", "/api/courses/" + encodeURIComponent(c.course_code));
      const sections = res.data?.sections || [];
      const bundle = findCompatibleSectionBundle(sections);
      if (bundle) fits.push({ ...c, bundle });
    } catch (err) {
      console.warn("Could not check sections for", c.course_code, err);
    }
  }

  if (!fits.length) {
    box.innerHTML = `<div class="muted">No 100–200 level multi-Hub suggestions had a complete non-conflicting section set. Try removing a selected section, widening the missing Hub list, or manually searching a Hub course.</div>`;
    return;
  }

  box.innerHTML = fits.map(c => {
    const fills = c.filledHubUnits && c.filledHubUnits.length ? c.filledHubUnits : [];
    const bundleText = c.bundle.map(sec => `${sec.section || sec.display_title || "Section"}: ${sec.days || ""} ${sec.start || ""}-${sec.end || ""}`).join(" | ");
    return `<div class="section-chip" onclick="loadSuggestedHubSections('${c.course_code.replace(/'/g,"\\'")}')">
      <b>${escapeHtml(c.course_code)} — ${escapeHtml(c.course_title)}</b>
      <div class="section-meta">
        <div><b>Fills:</b> ${fills.map(x => `<span class="tiny-pill">${escapeHtml(x)}</span>`).join(" ")}</div>
        <div class="muted">Compatible set found: ${escapeHtml(bundleText)}</div>
        <div class="muted">Click to load available sections.</div>
      </div>
    </div>`;
  }).join("");
}

async function loadSuggestedHubSections(code) {
  document.getElementById("semesterCourseQuery").value = code;
  await searchSemesterCourses();
}


function escapeHtml(str) { return String(str || "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;"); }


/* v19 current-semester visual overrides */
const COURSE_EVENT_COLORS_V19 = [
  {bg:'#dbeafe', border:'#93c5fd'}, {bg:'#dcfce7', border:'#86efac'},
  {bg:'#fef3c7', border:'#fcd34d'}, {bg:'#fce7f3', border:'#f9a8d4'},
  {bg:'#ede9fe', border:'#c4b5fd'}, {bg:'#ffedd5', border:'#fdba74'},
  {bg:'#ccfbf1', border:'#5eead4'}, {bg:'#e0e7ff', border:'#a5b4fc'}
];
function colorIndexForCourseV19(code){ let h=0; String(code||'').split('').forEach(ch=>h=(h*31+ch.charCodeAt(0))>>>0); return h % COURSE_EVENT_COLORS_V19.length; }
const originalDrawSectionEventV19 = drawSectionEvent;
drawSectionEvent = function(layer, sec, extraClass){
  const before=layer.children.length;
  originalDrawSectionEventV19(layer, sec, extraClass);
  if(extraClass) return;
  const colors=COURSE_EVENT_COLORS_V19[colorIndexForCourseV19(sec.course_code)];
  [...layer.children].slice(before).forEach(ev=>{ ev.style.background=colors.bg; ev.style.borderColor=colors.border; });
};
function v19SemesterLoadDefaults(){
  const name=document.getElementById('semesterName'); if(name && !name.value) name.value='Current Semester';
  const title=document.getElementById('semesterScheduleTitle'); if(title && !title.value) title.value='Current Semester Schedule';
}

window.addEventListener("load", () => {
  v19SemesterLoadDefaults();
  loadSemesterDraft();
  refreshDegreeTermPicker();
  renderSelectedSections();
  renderCalendar();
  requestAnimationFrame(() => { renderSelectedSections(); renderCalendar(); });
  setTimeout(() => { renderSelectedSections(); renderCalendar(); }, 150);
  window.addEventListener("resize", renderCalendar);
});

/* v25: hide Hub suggestions immediately after selecting one */
(function(){
  if (typeof loadSuggestedHubSections === 'function') {
    const oldLoadSuggestedHubSectionsV25 = loadSuggestedHubSections;
    loadSuggestedHubSections = async function(code){
      const box = document.getElementById('semesterHubSuggestions');
      if (box) {
        box.classList.add('flash-target');
        box.innerHTML = `<div class="muted">Loading ${escapeHtml(code)} into section search...</div>`;
      }
      await oldLoadSuggestedHubSectionsV25(code);
      if (box) {
        box.classList.remove('flash-target');
        box.classList.add('closed-after-select');
        box.style.display = 'none';
        box.innerHTML = `<div class="muted">Suggestions closed. Click “Suggest Hub Courses” to search again.</div>`;
      }
      const results = document.getElementById('semesterSectionResults');
      if (results) results.scrollIntoView({behavior:'smooth', block:'start'});
    };
  }
  if (typeof suggestSemesterHubCourses === 'function') {
    const oldSuggestSemesterHubCoursesV25 = suggestSemesterHubCourses;
    suggestSemesterHubCourses = async function(){
      const box = document.getElementById('semesterHubSuggestions');
      if (box) { box.classList.remove('closed-after-select'); box.style.display = 'block'; }
      return oldSuggestSemesterHubCoursesV25();
    };
  }
})();

</script>
"""

SCHEDULES_CONTENT = r"""
<div class="schedule-browser">
  <aside class="schedule-filter-panel">
    <h2>Student Schedules</h2>
    <p class="muted">Browse public degree plans by major, student, term, or course.</p>
    <select id="filterMajor"></select>
    <select id="filterGraduated">
      <option value="">All graduation statuses</option>
      <option value="false">Not graduated</option>
      <option value="true">Graduated</option>
    </select>
    <input id="filterText" placeholder="Search student, course, term...">
    <button onclick="loadSchedules()">Refresh Schedules</button>
  </aside>
  <section>
    <div id="scheduleResults" class="schedule-results-grid"><div class="muted">Loading schedules...</div></div>
  </section>
</div>
"""

SCHEDULES_SCRIPT = r"""
<script>
const SCHEDULE_TERM_ORDER = [
  'Transferred Courses',
  'Freshman Fall','Freshman Spring','Freshman Summer',
  'Sophomore Fall','Sophomore Spring','Sophomore Summer',
  'Junior Fall','Junior Spring','Junior Summer',
  'Senior Fall','Senior Spring','Senior Summer'
];
function scheduleYearBucket(term){
  const t=String(term||'');
  if(t.includes('Transferred')) return 'Transferred / AP';
  if(t.includes('Freshman')) return 'Freshman';
  if(t.includes('Sophomore')) return 'Sophomore';
  if(t.includes('Junior')) return 'Junior';
  if(t.includes('Senior')) return 'Senior';
  return 'Custom / Other';
}
function setupScheduleFilters() {
  const major = document.getElementById('filterMajor');
  major.innerHTML = `<option value="">All majors</option>`;
  Object.keys(MAJOR_DATA).forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m;
    major.appendChild(opt);
  });
  document.getElementById('filterText').addEventListener('input', () => loadSchedules(false));
  document.getElementById('filterMajor').addEventListener('change', () => loadSchedules(false));
  document.getElementById('filterGraduated').addEventListener('change', () => loadSchedules(false));
}
let LAST_SCHEDULES=[];
async function loadSchedules(fetchFresh=true) {
  if(fetchFresh || !LAST_SCHEDULES.length){
    const result = await api('GET', '/api/schedules', null, {silent:true});
    const schedules = result.data?.data || result.data || [];
    LAST_SCHEDULES = Array.isArray(schedules) ? schedules : [];
  }
  renderSchedules(LAST_SCHEDULES);
}
function scheduleMatchesMajor(s, majorFilter){
  if(!majorFilter) return true;
  const majors = Array.isArray(s.majors) ? s.majors : [s.major];
  return majors.map(x=>String(x||'').toLowerCase()).includes(majorFilter);
}
function renderSchedules(schedules) {
  const majorFilter = document.getElementById('filterMajor').value.toLowerCase();
  const text = document.getElementById('filterText').value.toLowerCase();
  const graduatedFilter = document.getElementById('filterGraduated').value;
  const container = document.getElementById('scheduleResults');
  container.innerHTML = '';
  const filtered = schedules.filter(s => {
    const haystack = JSON.stringify(s).toLowerCase();
    const gradOk = !graduatedFilter || String(Boolean(s.graduated)) === graduatedFilter;
    return scheduleMatchesMajor(s, majorFilter) && gradOk && (!text || haystack.includes(text));
  });
  if (!filtered.length) { container.innerHTML = `<div class="muted">No matching schedules found.</div>`; return; }
  filtered.forEach(s => {
    const card = document.createElement('article');
    card.className = 'schedule-card compact';
    const creator = s.creator?.displayName || s.creator?.email || 'Unknown student';
    const majors = Array.isArray(s.majors) && s.majors.length ? s.majors : [s.major || 'Unspecified'];
    const terms = s.terms || {};
    const entries = Object.entries(terms).sort(([a],[b]) => {
      const ia=SCHEDULE_TERM_ORDER.indexOf(a), ib=SCHEDULE_TERM_ORDER.indexOf(b);
      return (ia<0?999:ia)-(ib<0?999:ib) || a.localeCompare(b);
    });
    const buckets = {};
    entries.forEach(([term,courses]) => { const b=scheduleYearBucket(term); (buckets[b] ||= []).push([term,courses||[]]); });
    const bucketHtml = Object.entries(buckets).map(([bucket, list]) => `
      <div class="schedule-year-block">
        <div class="schedule-year-title">${escapeHtml(bucket)}</div>
        ${list.map(([term,courses]) => `
          <div class="schedule-term-mini">
            <b>${escapeHtml(term)}</b>
            ${(courses||[]).slice(0,10).map(c=>`<span class="mini-course-line">${escapeHtml(c.course_code || '')}</span>`).join('') || `<span class="muted">No courses</span>`}
            ${(courses||[]).length>10 ? `<span class="mini-course-line">+${(courses||[]).length-10} more</span>` : ''}
          </div>`).join('')}
      </div>`).join('');
    card.innerHTML = `
      <h3>${escapeHtml(s.title || 'Untitled Schedule')}</h3>
      <div class="schedule-meta-row">
        <span class="schedule-meta-pill">${escapeHtml(creator)}</span>
        ${majors.map(m=>`<span class="schedule-meta-pill">${escapeHtml(m)}</span>`).join('')}
        <span class="schedule-meta-pill">${s.graduated ? 'Graduated' : 'In progress'}</span>
      </div>
      ${s.comments ? `<p class="muted">${escapeHtml(s.comments)}</p>` : ''}
      ${bucketHtml}
    `;
    container.appendChild(card);
  });
}
function escapeHtml(str) { return String(str || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;'); }
window.addEventListener('load', () => { setupScheduleFilters(); loadSchedules(); });
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



# =============================================================================
# v28 patch: force visible save/load controls near title and move course comments
# to backend table endpoints instead of storing comments inside schedule JSON.
# =============================================================================
BASE_HTML = BASE_HTML.replace("</style>", r'''

/* v28: visible top controls and cleaner course-comment behavior */
.builder-top > div { width: 100%; }
#v28TopTools {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) auto;
  gap: 12px;
  align-items: start;
  width: 100%;
  margin: 10px 0 12px;
}
#v28MajorBox, #v28ActionBox {
  background: #ffffff;
  border: 1px solid #dbe4f0;
  border-radius: 14px;
  padding: 10px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}
#v28ActionBox { min-width: 260px; }
.v28-action-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
#v28ActionBox button { margin: 0; }
#lastSaveTimestampV28 { margin-top: 7px; font-size: 12px; color: #64748b; }
#v28ActionBox { background: transparent !important; border: 0 !important; box-shadow: none !important; padding: 0 !important; }
#v28ActionBox .settings-label { display:none !important; }
.clean-save-load-row { margin-top: 4px; }
#v28MajorBox .major-checkbox-grid, #v28MajorBox #majorCheckboxGrid {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 6px;
}
.course-card .comment-text { display: none !important; }
#commentModalText { min-height: 110px; }
@media (max-width: 900px) { #v28TopTools { grid-template-columns: 1fr; } #v28ActionBox { min-width: 0; } }
</style>''')

BASE_HTML = BASE_HTML.replace("</body>", r'''
<script>
(function(){
  function niceTime(iso){
    if(!iso) return 'never';
    const d = new Date(iso);
    if(Number.isNaN(d.getTime())) return 'never';
    return d.toLocaleString([], {month:'short', day:'numeric', hour:'numeric', minute:'2-digit'});
  }

  function updateLastSaveLabelV28(){
    const el = document.getElementById('lastSaveTimestampV28');
    if(!el) return;
    const t = localStorage.getItem('degreeScheduleServerSaveAt') || localStorage.getItem('degreeScheduleDraftSavedAt');
    el.textContent = 'Last save: ' + niceTime(t);
  }
  window.updateLastSaveLabelV28 = updateLastSaveLabelV28;

  function ensureVisibleTopToolsV28(){
    const top = document.querySelector('.builder-top > div');
    if(!top || document.getElementById('v28TopTools')) return;

    const tools = document.createElement('div');
    tools.id = 'v28TopTools';
    tools.innerHTML = `
      <div id="v28MajorBox">
        <div class="settings-label">Majors</div>
        <div id="v28MajorMount"></div>
      </div>
      <div id="v28ActionBox">
        <div class="v28-action-row clean-save-load-row">
          <button type="button" onclick="saveScheduleV28()">Save</button>
          <button type="button" class="secondary" onclick="loadMyScheduleV28()">Load saved</button>
        </div>
        <div id="lastSaveTimestampV28">Last save: never</div>
      </div>
    `;

    const title = document.getElementById('degreePlanTitle');
    if(title && title.parentElement) title.insertAdjacentElement('afterend', tools);
    else top.prepend(tools);

    if(typeof setupMajorCheckboxesV19 === 'function') setupMajorCheckboxesV19();
    const existingGrid = document.getElementById('majorCheckboxGrid');
    const mount = document.getElementById('v28MajorMount');
    if(existingGrid && mount && existingGrid.parentElement !== mount) mount.appendChild(existingGrid);
    const oldMajorShell = document.querySelector('.major-picker-shell');
    if(oldMajorShell) oldMajorShell.style.display = 'none';

    updateLastSaveLabelV28();
  }
  window.ensureVisibleTopToolsV28 = ensureVisibleTopToolsV28;

  window.saveScheduleV28 = async function(){
    if(typeof saveSchedule !== 'function') return;
    const result = await saveSchedule();
    const now = new Date().toISOString();
    localStorage.setItem('degreeScheduleServerSaveAt', now);
    localStorage.setItem('degreeScheduleDraftSavedAt', now);
    updateLastSaveLabelV28();
    if(typeof showToast === 'function') showToast('Saved degree plan.');
    return result;
  };

  window.loadMyScheduleV28 = async function(){
    if(typeof loadMySchedule !== 'function') return;
    const result = await loadMySchedule();
    updateLastSaveLabelV28();
    if(typeof showToast === 'function') showToast('Loaded saved degree plan.');
    return result;
  };

  function actualCourseCodeForCommentsV28(raw){
    const s = String(raw || '').trim();
    const paren = s.match(/\(([A-Z]{2,}\s*[A-Z]{0,3}\s*\d{3}[A-Z]?)\)/i);
    if(paren) return paren[1].replace(/\s+/g, ' ').toUpperCase();
    const direct = s.match(/([A-Z]{2,}\s*[A-Z]{0,3}\s*\d{3}[A-Z]?)/i);
    if(direct) return direct[1].replace(/\s+/g, ' ').toUpperCase();
    return s;
  }
  window.actualCourseCodeForCommentsV28 = actualCourseCodeForCommentsV28;

  async function fetchCourseCommentsV28(code){
    const clean = actualCourseCodeForCommentsV28(code);
    const result = await api('GET', '/api/course-comments?course_code=' + encodeURIComponent(clean));
    if(Array.isArray(result.data)) return result.data;
    if(Array.isArray(result.data?.comments)) return result.data.comments;
    if(Array.isArray(result.data?.data?.comments)) return result.data.data.comments;
    return [];
  }

  window.openCommentModal = async function(event, button){
    event.stopPropagation();
    COMMENT_CARD = button.closest('.course-card');
    const raw = COMMENT_CARD?.dataset?.code || '';
    const code = actualCourseCodeForCommentsV28(raw);
    document.getElementById('commentModalTitle').textContent = `Comments for ${code}`;
    document.getElementById('commentModalText').value = '';
    document.getElementById('commentModal').classList.add('visible');
    await loadOtherStudentComments(code);
  };

  window.saveModalComment = async function(){
    if(!COMMENT_CARD) return;
    const raw = COMMENT_CARD.dataset.code || '';
    const code = actualCourseCodeForCommentsV28(raw);
    const body = document.getElementById('commentModalText').value.trim();
    if(!body){ if(typeof showToast === 'function') showToast('Write a comment first.'); return; }
    const result = await api('POST', '/api/course-comments', { course_code: code, body });
    if(result.status >= 200 && result.status < 300){
      COMMENT_CARD.dataset.commentCount = String(Number(COMMENT_CARD.dataset.commentCount || '0') + 1);
      const countEl = COMMENT_CARD.querySelector('.comment-count');
      if(countEl){ const n = Number(COMMENT_CARD.dataset.commentCount || '1'); countEl.textContent = n > 9 ? '9+' : String(n); }
      document.getElementById('commentModalText').value = '';
      await loadOtherStudentComments(code);
      if(typeof showToast === 'function') showToast('Comment saved for ' + code + '.');
    }
  };

  window.loadOtherStudentComments = async function(code){
    const box = document.getElementById('otherStudentComments');
    if(!box) return;
    const clean = actualCourseCodeForCommentsV28(code);
    box.innerHTML = `<div class="muted">Loading comments for ${clean}...</div>`;
    try{
      const comments = await fetchCourseCommentsV28(clean);
      if(!comments.length){ box.innerHTML = `<div class="muted">No course comments yet.</div>`; return; }
      box.innerHTML = comments.slice(0,50).map(c => {
        const who = c.creator?.displayName || c.creator?.email || c.author || 'Student';
        const when = c.createdAt ? new Date(c.createdAt).toLocaleDateString() : '';
        const text = c.body || c.comment || c.text || '';
        return `<div class="section-option"><b>${escapeHtml(who)}</b> <span class="muted">${escapeHtml(when)}</span><br>${escapeHtml(text)}</div>`;
      }).join('');
    }catch(err){ box.innerHTML = `<div class="muted">Could not load comments.</div>`; }
  };

  if(typeof buildScheduleJson === 'function'){
    const previousBuildScheduleJsonV28 = buildScheduleJson;
    buildScheduleJson = function(){
      const schedule = previousBuildScheduleJsonV28();
      Object.values(schedule.terms || {}).forEach(courses => {
        (courses || []).forEach(c => { delete c.comments; delete c.comment; });
      });
      return schedule;
    };
  }

  window.addEventListener('load', () => {
    ensureVisibleTopToolsV28();
    setTimeout(ensureVisibleTopToolsV28, 200);
    setTimeout(ensureVisibleTopToolsV28, 900);
    updateLastSaveLabelV28();
  });
})();
</script>
</body>''')



# v30: GCI duplicate fix, stronger plan title, visible Save/Load/Major tools, graduated boolean, duplicate required cleanup
BASE_HTML = BASE_HTML.replace("</body>", r'''
<style>
#v30TopTools {
  display: grid;
  grid-template-columns: minmax(280px, 1.25fr) minmax(250px, 0.75fr);
  gap: 12px;
  margin: 10px 0 12px;
}
#v30MajorBox, #v30ActionBox {
  background: #ffffff;
  border: 1px solid #dbe4f0;
  border-radius: 14px;
  padding: 10px 12px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}
#v30TopTools .settings-label { font-weight: 700; font-size: 13px; color: #334155; margin-bottom: 7px; }
#v30MajorBox #majorCheckboxGrid, #v30MajorBox .major-checkbox-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 6px;
}
.v30-action-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.v30-action-row button { margin: 0; }
.v30-last-save { margin-top: 8px; font-size: 12px; color: #64748b; }
.v30-graduated {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  font-size: 13px;
  color: #334155;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 8px 9px;
}
.v30-graduated input { width: auto; margin: 0; }
@media (max-width: 900px) { #v30TopTools { grid-template-columns: 1fr; } }
</style>
<script>
(function(){
  function fallbackNameFromEmailV30(email){
    if(!email || !String(email).includes('@')) return 'My';
    const raw = String(email).split('@')[0]
      .replace(/[0-9]+$/g, '')
      .replace(/[._-]+/g, ' ')
      .trim();
    if(!raw) return 'My';
    return raw.split(/\s+/).map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(' ');
  }

  function bestUserNameV30(){
    const candidates = [];
    try { if(window.CURRENT_USER) candidates.push(window.CURRENT_USER); } catch(e) {}
    try { if(typeof CURRENT_USER !== 'undefined' && CURRENT_USER) candidates.push(CURRENT_USER); } catch(e) {}
    try { const cached = JSON.parse(localStorage.getItem('lastKnownUser') || 'null'); if(cached) candidates.push(cached); } catch(e) {}
    for(const u of candidates){
      const display = (u.displayName || '').trim();
      if(display && display.toLowerCase() !== 'student') return display.split(/\s+/)[0];
      const emailName = fallbackNameFromEmailV30(u.email || '');
      if(emailName !== 'My') return emailName;
    }
    const email = localStorage.getItem('loginEmail') || localStorage.getItem('registerEmail') || '';
    return fallbackNameFromEmailV30(email);
  }

  async function refreshUserForTitleV30(){
    try{
      const res = await fetch('/proxy/api/auth/me', {credentials:'same-origin'});
      const data = await res.json();
      if(data && data.user){
        window.CURRENT_USER = data.user;
        try { CURRENT_USER = data.user; } catch(e) {}
        localStorage.setItem('lastKnownUser', JSON.stringify(data.user));
      }
    }catch(e) {}
    return setDegreePlanTitleV30();
  }

  function setDegreePlanTitleV30(){
    const name = bestUserNameV30();
    const title = `${name}'s Degree Plan`;
    const h = document.getElementById('degreePlanTitle');
    const input = document.getElementById('scheduleTitle');
    if(h) h.textContent = title;
    if(input) input.value = title;
    return title;
  }
  window.setDegreePlanTitleV30 = setDegreePlanTitleV30;
  window.updateDegreePlanTitleV26 = setDegreePlanTitleV30;
  window.updateDegreePlanTitleV25 = setDegreePlanTitleV30;
  window.updateDegreePlanTitleV24 = setDegreePlanTitleV30;

  function niceTimeV30(iso){
    if(!iso) return 'never';
    const d = new Date(iso);
    if(Number.isNaN(d.getTime())) return 'never';
    return d.toLocaleString([], {month:'short', day:'numeric', hour:'numeric', minute:'2-digit'});
  }
  function updateLastSaveLabelV30(){
    const el = document.getElementById('lastSaveTimestampV30');
    if(!el) return;
    const t = localStorage.getItem('degreeScheduleServerSaveAt') || localStorage.getItem('degreeScheduleDraftSavedAt');
    el.textContent = 'Last save: ' + niceTimeV30(t);
  }
  window.updateLastSaveLabelV30 = updateLastSaveLabelV30;

  function ensureVisibleTopToolsV30(){
    const top = document.querySelector('.builder-top > div');
    if(!top) return;

    let tools = document.getElementById('v30TopTools');
    if(!tools){
      tools = document.createElement('div');
      tools.id = 'v30TopTools';
      tools.innerHTML = `
        <div id="v30MajorBox">
          <div class="settings-label">Majors</div>
          <div id="v30MajorMount"></div>
        </div>
        <div id="v30ActionBox">
          <div class="settings-label">Schedule</div>
          <div class="v30-action-row">
            <button type="button" onclick="saveScheduleV30()">Save</button>
            <button type="button" class="secondary" onclick="loadMyScheduleV30()">Load saved</button>
          </div>
          <label class="v30-graduated"><input id="graduatedCheckbox" type="checkbox" onchange="saveLocalDegreeDraft()"> Graduated / finished degree</label>
          <div id="lastSaveTimestampV30" class="v30-last-save">Last save: never</div>
        </div>
      `;
      const title = document.getElementById('degreePlanTitle');
      if(title) title.insertAdjacentElement('afterend', tools);
      else top.prepend(tools);
    }

    if(typeof setupMajorCheckboxesV19 === 'function') setupMajorCheckboxesV19();
    const existingGrid = document.getElementById('majorCheckboxGrid');
    const mount = document.getElementById('v30MajorMount');
    if(existingGrid && mount && existingGrid.parentElement !== mount) mount.appendChild(existingGrid);
    const oldMajorShell = document.querySelector('.major-picker-shell');
    if(oldMajorShell) oldMajorShell.style.display = 'none';

    ['scheduleToolsV25','scheduleToolsV26','majorToolsV25','majorToolsV26'].forEach(id => {
      const el = document.getElementById(id);
      if(el) el.remove();
    });

    updateLastSaveLabelV30();
    setDegreePlanTitleV30();
    dedupeRequiredHeadingsV30();
  }
  window.ensureVisibleTopToolsV30 = ensureVisibleTopToolsV30;

  window.saveScheduleV30 = async function(){
    if(typeof saveSchedule !== 'function') return;
    const result = await saveSchedule();
    if(!result || result.status === undefined || result.status < 400){
      const now = new Date().toISOString();
      localStorage.setItem('degreeScheduleServerSaveAt', now);
      localStorage.setItem('degreeScheduleDraftSavedAt', now);
      updateLastSaveLabelV30();
    }
    return result;
  };

  window.loadMyScheduleV30 = async function(){
    if(typeof loadMySchedule !== 'function') return;
    const result = await loadMySchedule();
    setTimeout(()=>{ ensureVisibleTopToolsV30(); updateGraduatedCheckboxFromScheduleV30(); }, 0);
    updateLastSaveLabelV30();
    return result;
  };

  function dedupeRequiredHeadingsV30(){
    const panel = document.getElementById('requiredPanel');
    if(!panel) return;
    panel.querySelectorAll('.required-bank > h2, .required-bank > p.muted').forEach(el => el.remove());
    const menu = panel.querySelector('.required-scroll-menu') || panel;
    const headingBlocks = [...menu.querySelectorAll('.required-heading-v20')];
    headingBlocks.forEach((el, i) => { if(i > 0) el.remove(); });
    const headings = [...menu.querySelectorAll('h2')].filter(h => h.textContent.trim() === 'Required Courses');
    headings.forEach((h, i) => {
      if(i > 0 || !h.closest('.required-heading-v20')) {
        const p = h.nextElementSibling;
        if(p && p.classList.contains('muted') && p.textContent.includes('Already-placed')) p.remove();
        h.remove();
      }
    });
    const muted = [...menu.querySelectorAll('p.muted')].filter(p => p.textContent.includes('Already-placed requirements'));
    muted.forEach((p, i) => { if(i > 0 || !p.closest('.required-heading-v20')) p.remove(); });
  }
  window.dedupeRequiredHeadingsV30 = dedupeRequiredHeadingsV30;

  function hubFamilyCountsV30(){
    const counts = {};
    document.querySelectorAll('.course-card').forEach(card => {
      let units = [];
      try { units = JSON.parse(card.dataset.hubUnits || '[]'); } catch(e) { units = []; }
      units.forEach(unit => {
        const fam = (typeof hubFamily === 'function') ? hubFamily(unit) : String(unit || '').toLowerCase();
        if(!fam) return;
        counts[fam] = (counts[fam] || 0) + 1;
      });
    });
    return counts;
  }

  window.getUnfulfilledHubUnits = function(){
    const counts = hubFamilyCountsV30();
    const seenReq = {};
    return HUB_UNITS.filter(unit => {
      const fam = (typeof hubFamily === 'function') ? hubFamily(unit) : String(unit || '').toLowerCase();
      seenReq[fam] = (seenReq[fam] || 0) + 1;
      const requiredOccurrence = seenReq[fam];
      return (counts[fam] || 0) < requiredOccurrence;
    });
  };

  window.setupHubChecklist = function(unfulfilled){
    const box = document.getElementById('hubChecklist');
    if(!box) return;
    const missing = new Set(unfulfilled || getUnfulfilledHubUnits());
    box.innerHTML = HUB_UNITS.map(unit => {
      const done = !missing.has(unit);
      return `<label class="hub-track-item ${done ? 'done' : 'missing'}"><input type="checkbox" disabled ${done ? 'checked' : ''}> ${escapeHtml(unit)}</label>`;
    }).join('');
  };

  function updateGraduatedCheckboxFromScheduleV30(schedule){
    const box = document.getElementById('graduatedCheckbox');
    if(!box) return;
    let val = false;
    if(schedule && typeof schedule.graduated === 'boolean') val = schedule.graduated;
    else {
      try { val = !!JSON.parse(localStorage.getItem('degreeScheduleDraft') || '{}').graduated; } catch(e) { val = false; }
    }
    box.checked = val;
  }
  window.updateGraduatedCheckboxFromScheduleV30 = updateGraduatedCheckboxFromScheduleV30;

  if(typeof buildScheduleJson === 'function'){
    const prevBuildV30 = buildScheduleJson;
    buildScheduleJson = function(){
      const schedule = prevBuildV30();
      schedule.title = setDegreePlanTitleV30();
      const grad = document.getElementById('graduatedCheckbox');
      schedule.graduated = !!(grad && grad.checked);
      return schedule;
    };
  }

  if(typeof renderSchedule === 'function'){
    const prevRenderV30 = renderSchedule;
    renderSchedule = function(schedule){
      prevRenderV30(schedule);
      setTimeout(()=>{
        ensureVisibleTopToolsV30();
        updateGraduatedCheckboxFromScheduleV30(schedule);
        if(typeof setupHubChecklist === 'function') setupHubChecklist(getUnfulfilledHubUnits());
      }, 0);
    };
  }

  if(typeof updateHeaderAuth === 'function'){
    const prevHeaderV30 = updateHeaderAuth;
    updateHeaderAuth = async function(){
      const result = await prevHeaderV30();
      await refreshUserForTitleV30();
      return result;
    };
  }

  window.addEventListener('load', () => {
    setTimeout(async()=>{ await refreshUserForTitleV30(); ensureVisibleTopToolsV30(); updateGraduatedCheckboxFromScheduleV30(); if(typeof setupHubChecklist === 'function') setupHubChecklist(getUnfulfilledHubUnits()); }, 100);
    setTimeout(()=>{ ensureVisibleTopToolsV30(); dedupeRequiredHeadingsV30(); setDegreePlanTitleV30(); }, 500);
    setTimeout(()=>{ ensureVisibleTopToolsV30(); dedupeRequiredHeadingsV30(); setDegreePlanTitleV30(); }, 1200);
  });
})();
</script>
</body>''')

if __name__ == "__main__":
    print("31")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", debug=True, port=port)
