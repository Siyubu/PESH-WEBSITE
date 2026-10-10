import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";

const SLIDES = [
  { img: "hero1.jpeg", title: "Bridging the Digital Divide", text: "We equip youth, children, and adults in Rwanda with digital skills and access to technology, empowering them to thrive in a digital world.", cta: "Get Involved", to: "/#contact" },
  { img: "hero2.jpeg", title: "Empowering the Next Generation", text: "We provide hands on training and mentorship to prepare youth for real world digital opportunities and a successful future.", cta: "Our Programs", to: "/#programs" },
  { img: "hero3.jpeg", title: "Creating Opportunities", text: "Through technology, mentorship, and community support, we open doors for education, skill-building, and meaningful employment.", cta: "Learn More", to: "/#about" },
];

const PROGRAMS = [
  { img: "training1.jpeg", title: "Digital Training", body: "We provide hands-on training in computer skills, internet use, and digital tools to prepare youth for real-world opportunities.", list: [["Tue & Thu:", "6:00 PM – 8:00 PM (Youth)"], ["Saturday:", "9:00 AM – 12:00 PM (Children)"]] },
  { img: "space.jpeg", title: "Device Support", body: "Access to a personal computer can significantly enhance learning and productivity. For those without one, we provide computers at our hub where individuals can come, use them for learning, and return them after use." },
  { img: "mentor.jpeg", title: "Mentorship", body: "We mentor young women, many of whom go on to volunteer at our hub. They play a key role in teaching children during Saturday sessions in the school term, and we extend these sessions by adding two additional days during school holidays." },
  { img: "community.jpeg", title: "Community Outreach", body: "We collaborate with local government to engage community groups and promote digital awareness. Through our outreach programs, we help individuals and communities understand and use technology to improve their daily lives." },
];

function useHashScroll() {
  const { hash } = useLocation();
  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [hash]);
}

function Hero() {
  const [i, setI] = useState(0);
  const timer = useRef(null);
  const go = (n) => setI((n + SLIDES.length) % SLIDES.length);

  useEffect(() => {
    timer.current = setInterval(() => setI((x) => (x + 1) % SLIDES.length), 5000);
    return () => clearInterval(timer.current);
  }, []);

  return (
    <div className="hero">
      <div className="arrow left" onClick={() => go(i - 1)} role="button" aria-label="Previous slide">&#10094;</div>
      <div className="arrow right" onClick={() => go(i + 1)} role="button" aria-label="Next slide">&#10095;</div>
      <div className="hero-slider" style={{ transform: `translateX(${-i * 100}%)` }}>
        {SLIDES.map((s) => (
          <div className="hero-slide" key={s.img}>
            <img src={`/images/${s.img}`} className="hero-img" alt="" />
            <img src="/images/logo.jpg" className="watermark" alt="" />
            <div className="hero-content">
              <h1>{s.title}</h1>
              <p>{s.text}</p>
              <Link to={s.to} className="btn">{s.cta}</Link>
            </div>
          </div>
        ))}
      </div>
      <div className="dots">
        {SLIDES.map((s, n) => <span key={s.img} className={`dot ${n === i ? "active" : ""}`} onClick={() => go(n)} />)}
      </div>
    </div>
  );
}

function ContactForm() {
  const [state, setState] = useState("idle");
  async function submit(e) {
    e.preventDefault();
    const form = e.currentTarget;
    try {
      const res = await fetch("https://formspree.io/f/xzdkoozg", { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error("bad response");
      setState("ok");
      form.reset();
    } catch {
      setState("error");
    }
  }
  return (
    <form onSubmit={submit}>
      <input type="text" name="name" placeholder="Your Name" required />
      <input type="email" name="email" placeholder="Your Email" required />
      <textarea name="message" placeholder="Your Message" required />
      <button type="submit">Send Message</button>
      {state === "ok" && <p style={{ color: "green", marginTop: 10 }}>Message sent successfully! Thank you.</p>}
      {state === "error" && <p style={{ color: "red", marginTop: 10 }}>Oops! Something went wrong. Please try again.</p>}
    </form>
  );
}

export default function Home() {
  useHashScroll();
  return (
    <>
      <Hero />
      <section id="about">
        <h2>About Us</h2>
        <p>
          PESH is a youth-led initiative committed to empowering people in Rwanda through digital access, skills training, and community
          support. We believe that everyone, especially the younger generation, deserves the opportunity to learn, grow, and succeed in
          today’s digital world. Through our programs, we provide access to technology, mentorship, and practical skills with a hope to open
          doors to education and employment.
        </p>
        <img src="/images/about.jpeg" className="about-img" alt="PESH learners" />
      </section>
      <section id="programs">
        <h2>Our Programs</h2>
        <div className="cards">
          {PROGRAMS.map((p) => (
            <div className="card" key={p.title}>
              <img src={`/images/${p.img}`} alt="" />
              <h3>{p.title}</h3>
              <p>{p.body}</p>
              {p.list && (
                <ul className="program-list">
                  {p.list.map(([k, v]) => <li key={k}><strong>{k}</strong> {v}</li>)}
                </ul>
              )}
            </div>
          ))}
        </div>
      </section>
      <section id="courses">
        <h2>Learn Online</h2>
        <p>
          Follow our lessons at your own pace: Microsoft Word, Microsoft Excel, the Internet and AI, and Scratch programming. Create a free account to track your
          progress, and earn a PESH certificate when you complete a course.
        </p>
        <Link to="/courses" className="btn">Browse Courses</Link>
      </section>
      <section id="contact">
        <h2>Contact Us</h2>
        <ContactForm />
      </section>
    </>
  );
}
