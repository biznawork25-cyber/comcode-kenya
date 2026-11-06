import billingPlans from "../../billing-plans.json";

const curriculum = [
  {
    number: "01",
    title: "Foundational mathematics",
    description:
      "Build the mathematical intuition behind every great computer scientist.",
    topics: ["Calculus", "Linear algebra", "Discrete math", "Probability"],
    className: "math",
  },
  {
    number: "02",
    title: "Core computer science",
    description:
      "Understand how software works, from the first line of code to the operating system.",
    topics: ["Programming", "Data structures", "Algorithms", "Systems"],
    className: "core",
  },
  {
    number: "03",
    title: "Advanced specializations",
    description:
      "Go deeper into the fields shaping the future of technology.",
    topics: ["Artificial intelligence", "Security", "Cloud systems", "Capstone"],
    className: "specializations",
  },
];

const planCopy: Record<string, { detail: string; description: string }> = {
  weekly: {
    detail: "A focused start",
    description: "Explore the learning experience at your own pace.",
  },
  monthly: {
    detail: "Room to grow",
    description: "Build a steady study rhythm and keep your momentum.",
  },
  yearly: {
    detail: "Best value",
    description: "Make a long-term investment in your CS education.",
  },
};

const plans = billingPlans.map((plan) => ({
  ...plan,
  ...planCopy[plan.id],
  price: `KSh ${new Intl.NumberFormat("en-KE").format(plan.amount_kes)}`,
  billingPeriod: `per ${plan.interval}`,
  featured: plan.id === "yearly",
}));

const platformFeatures = [
  {
    icon: "▤",
    category: "LEARN",
    title: "Courses & resources",
    description:
      "Structured courses with guided lessons, lecture notes, video explainers, and materials to take offline.",
  },
  {
    icon: "✓",
    category: "PRACTISE",
    title: "Quizzes & examinations",
    description:
      "Low-pressure practice, assignments, and timed exams with clear feedback and automatic marking.",
  },
  {
    icon: "✳",
    category: "GET UNSTUCK",
    title: "A step-by-step AI tutor",
    description:
      "Ask questions in context, get a concept explained another way, and work through problems one step at a time.",
  },
  {
    icon: "↗",
    category: "SEE YOUR GROWTH",
    title: "Progress & recommendations",
    description:
      "Follow grades, topic mastery, and study progress, with suggestions for what to revisit next.",
  },
  {
    icon: "◎",
    category: "LEARN TOGETHER",
    title: "Student community",
    description:
      "Discuss challenging ideas, share questions, and learn alongside a community of curious students.",
  },
  {
    icon: "⌘",
    category: "TEACH & GUIDE",
    title: "Instructor workspace",
    description:
      "Give teachers and administrators tools to manage courses, publish assessments, and follow cohort progress.",
  },
  {
    icon: "✦",
    category: "CELEBRATE MILESTONES",
    title: "Certificates & achievements",
    description:
      "Recognize completed courses and meaningful milestones as students make their way through the curriculum.",
  },
  {
    icon: "◷",
    category: "STAY IN THE LOOP",
    title: "Helpful notifications",
    description:
      "Keep deadlines, new course materials, feedback, and learning reminders in one easy-to-follow place.",
  },
];

const architecture = [
  { label: "WEBSITE", value: "Next.js + TypeScript" },
  { label: "MOBILE APP", value: "React Native + Expo" },
  { label: "API", value: "Python + FastAPI" },
  { label: "DATABASE", value: "PostgreSQL" },
  { label: "PAYMENTS", value: "Paystack + M-Pesa (Daraja)" },
  { label: "AI & FILES", value: "Tutor + cloud storage" },
  { label: "DEPLOYMENT", value: "Cloud-ready foundation" },
];

const buildPhases = [
  {
    number: "01",
    title: "Plan the system",
    description: "Confirm users, learning journeys, and the shared platform architecture.",
  },
  {
    number: "02",
    title: "Design the experience",
    description: "Create clear, accessible student, instructor, and mobile interfaces.",
  },
  {
    number: "03",
    title: "Build the foundation",
    description: "Set up the API, database, accounts, and role-based access.",
  },
  {
    number: "04",
    title: "Create the learning tools",
    description: "Deliver courses, resources, practice, exams, and progress tracking.",
  },
  {
    number: "05",
    title: "Add the AI tutor",
    description: "Bring lesson-aware, step-by-step learning support into the platform.",
  },
  {
    number: "06",
    title: "Subscription billing",
    description: "Connect Paystack cards and M-Pesa prompts with verified payment updates.",
  },
  {
    number: "07",
    title: "Test and launch",
    description: "Validate sandbox payments, prepare deployment, and improve from feedback.",
  },
];

function ArrowIcon() {
  return (
    <svg
      aria-hidden="true"
      className="arrow-icon"
      fill="none"
      viewBox="0 0 20 20"
    >
      <path d="M4.167 10h11.666M10 4.167 15.833 10 10 15.833" />
    </svg>
  );
}

export default function Home() {
  return (
    <>
      <header className="site-header">
        <a aria-label="ComCode home" className="brand" href="#">
          <span aria-hidden="true" className="brand-mark">
            c
          </span>
          <span>comcode</span>
        </a>
        <nav aria-label="Main navigation" className="main-nav">
          <a href="#curriculum">Curriculum</a>
          <a href="#platform">Platform</a>
          <a href="#roadmap">Roadmap</a>
          <a href="#plans">Plans</a>
        </nav>
        <div className="header-actions">
          <a className="sign-in" href="#start">
            Sign in
          </a>
          <a className="button button-dark button-small" href="#curriculum">
            Start learning <ArrowIcon />
          </a>
        </div>
      </header>

      <main>
        <section aria-labelledby="hero-title" className="hero page-shell">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              A clearer path into computer science
            </div>
            <h1 id="hero-title">
              Learn computer science
              <br />
              <span>by understanding it.</span>
            </h1>
            <p className="hero-description">
              A complete, interactive CS education—from foundational
              mathematics to advanced systems. Built around the way
              universities teach, and the way you actually learn.
            </p>
            <div className="hero-actions" id="start">
              <a className="button button-dark" href="#curriculum">
                Explore the curriculum <ArrowIcon />
              </a>
              <a className="text-link" href="#lesson">
                See how lessons work
              </a>
            </div>
            <div className="hero-note">
              <span aria-hidden="true" className="note-check">
                ✓
              </span>
              Start with the fundamentals. Go as far as you want.
            </div>
          </div>

          <div aria-label="Interactive lesson preview" className="hero-visual">
            <div className="visual-topline">
              <span>INSIDE A LESSON</span>
              <span className="live-indicator">● &nbsp;Interactive</span>
            </div>
            <div className="lesson-card">
              <div className="lesson-meta">
                <span>ALGORITHMS</span>
                <span>LESSON 04 · 12 MIN</span>
              </div>
              <h2>Why does Big-O matter?</h2>
              <p>
                It describes how an algorithm&apos;s work grows as your input
                gets larger.
              </p>
              <div className="complexity-chart" aria-label="Growth rates chart">
                <div className="chart-labels">
                  <span>WORK</span>
                  <span>INPUT SIZE →</span>
                </div>
                <div className="chart-area">
                  <div className="chart-grid" />
                  <svg
                    aria-hidden="true"
                    className="chart-lines"
                    preserveAspectRatio="none"
                    viewBox="0 0 340 112"
                  >
                    <path className="line-quadratic" d="M8 104 C70 102 95 94 130 72 S195 27 230 12 S296 5 332 3" />
                    <path className="line-linear" d="M8 104 C78 94 152 77 218 55 S290 34 332 21" />
                    <path className="line-log" d="M8 104 C60 75 110 58 165 47 S275 34 332 29" />
                    <path className="line-constant" d="M8 91 C110 90 220 89 332 88" />
                  </svg>
                </div>
                <div className="chart-legend">
                  <span><i className="legend-dot quadratic" /> O(n²)</span>
                  <span><i className="legend-dot linear" /> O(n)</span>
                  <span><i className="legend-dot log" /> O(log n)</span>
                  <span><i className="legend-dot constant" /> O(1)</span>
                </div>
              </div>
              <div className="lesson-question">
                <span className="question-number">01</span>
                <span>Which grows slowest as the input gets bigger?</span>
                <span aria-hidden="true" className="question-arrow">↗</span>
              </div>
              <div className="lesson-progress">
                <span>YOUR PROGRESS</span>
                <span>4 of 9 concepts</span>
                <div className="progress-track"><span /></div>
              </div>
            </div>
            <div className="visual-caption">
              <span className="caption-mark">✳</span>
              Learn the idea. Then try it yourself.
            </div>
          </div>
        </section>

        <section aria-labelledby="curriculum-title" className="curriculum-section" id="curriculum">
          <div className="page-shell">
            <div className="section-heading">
              <div>
                <div className="eyebrow">A complete education, thoughtfully structured</div>
                <h2 id="curriculum-title">
                  The whole field.
                  <br />
                  <span>One connected curriculum.</span>
                </h2>
              </div>
              <p>
                Follow a clear path from first principles to advanced practice,
                with every subject building on what came before.
              </p>
            </div>

            <div className="curriculum-grid">
              {curriculum.map((pillar) => (
                <article className={`pillar-card ${pillar.className}`} key={pillar.number}>
                  <div className="pillar-top">
                    <span className="pillar-number">{pillar.number}</span>
                    <span className="pillar-icon" aria-hidden="true">
                      {pillar.className === "math" ? "∑" : pillar.className === "core" ? "{ }" : "↗"}
                    </span>
                  </div>
                  <h3>{pillar.title}</h3>
                  <p>{pillar.description}</p>
                  <div className="topic-list">
                    {pillar.topics.map((topic) => (
                      <span key={topic}>{topic}</span>
                    ))}
                  </div>
                  <a className="card-link" href="#lesson">
                    Explore this pillar <ArrowIcon />
                  </a>
                </article>
              ))}
            </div>
            <div className="curriculum-footnote">
              <span className="footnote-icon" aria-hidden="true">◎</span>
              Structured around internationally recognized computer science curricula
              <span className="footnote-rule" />
              <a href="#lesson">See a sample lesson <ArrowIcon /></a>
            </div>
          </div>
        </section>

        <section aria-labelledby="lesson-title" className="lesson-section page-shell" id="lesson">
          <div className="lesson-section-copy">
            <div className="eyebrow">Built for understanding, not memorizing</div>
            <h2 id="lesson-title">
              Make every
              <br />
              <span>concept click.</span>
            </h2>
            <p>
              Short explanations, worked examples, and interactive checkpoints
              help you connect the theory to the code—and know when you&apos;ve
              really got it.
            </p>
            <a className="text-link" href="#plans">
              Find your place to start <ArrowIcon />
            </a>
          </div>
          <div className="worked-example">
            <div className="example-header">
              <span>CONCEPT IN PRACTICE</span>
              <span className="example-tag">ALGORITHMS · BIG-O</span>
            </div>
            <h3>Count the work, not the seconds.</h3>
            <p className="example-description">
              This loop visits each item once. If the list doubles, the work
              doubles too.
            </p>
            <div className="code-window">
              <div className="code-title"><span /> <span /> <span /> <label>find_item.py</label></div>
              <pre><code><span className="code-muted">1</span>  <span className="code-purple">for</span> item <span className="code-purple">in</span> items:{"\n"}<span className="code-muted">2</span>      <span className="code-purple">if</span> item == target:{"\n"}<span className="code-muted">3</span>          <span className="code-blue">return</span> item</code></pre>
            </div>
            <div className="example-answer">
              <span className="answer-icon">↗</span>
              <span><strong>Your turn</strong> &nbsp;What happens when the list has 1,000 items?</span>
              <span className="answer-action">Try it <ArrowIcon /></span>
            </div>
            <div className="example-footer">
              <span>01 / 09</span>
              <div className="example-progress"><span /></div>
              <span>Complexity basics</span>
            </div>
          </div>
        </section>

        <section aria-label="Learning progress" className="mastery-section">
          <div className="mastery-inner page-shell">
            <div className="mastery-intro">
              <span className="mastery-overline">YOUR LEARNING, MADE VISIBLE</span>
              <h2>Progress you can feel.</h2>
              <p>See what you know, what you&apos;re building, and what to learn next.</p>
            </div>
            <div className="mastery-stat">
              <div className="stat-ring"><span>71<small>%</small></span></div>
              <span>Foundations</span>
              <small>Growing steadily</small>
            </div>
            <div className="mastery-stat">
              <div className="stat-ring ring-teal"><span>54<small>%</small></span></div>
              <span>Core CS</span>
              <small>In progress</small>
            </div>
            <div className="mastery-stat">
              <div className="stat-ring ring-sand"><span>12<small>%</small></span></div>
              <span>Specializations</span>
              <small>Ready when you are</small>
            </div>
          </div>
        </section>

        <section
          aria-labelledby="platform-title"
          className="platform-section"
          id="platform"
        >
          <div className="page-shell">
            <div className="platform-heading">
              <div>
                <div className="eyebrow">More than a place to watch lessons</div>
                <h2 id="platform-title">
                  Everything you need
                  <br />
                  <span>to keep moving forward.</span>
                </h2>
              </div>
              <p>
                A connected learning space for university and college students,
                with the tools to learn, practise, get support, and see how far
                they&apos;ve come.
              </p>
            </div>

            <div className="feature-grid">
              {platformFeatures.map((feature) => (
                <article className="feature-card" key={feature.title}>
                  <div className="feature-card-top">
                    <span aria-hidden="true" className="feature-icon">{feature.icon}</span>
                    <span className="feature-category">{feature.category}</span>
                  </div>
                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                </article>
              ))}
            </div>

            <div className="shared-platform">
              <div className="shared-copy">
                <span className="shared-label">ONE LEARNING ACCOUNT</span>
                <h3>Pick up wherever you left off.</h3>
                <p>
                  Start a lesson on your laptop. Review notes on your phone.
                  Your courses and learning progress belong to one connected
                  platform—not two separate products.
                </p>
                <div className="device-labels">
                  <span><i className="device-dot web-dot" /> WEB</span>
                  <span><i className="device-dot mobile-dot" /> ANDROID &amp; iOS</span>
                  <span><i className="device-dot sync-dot" /> SHARED PROGRESS</span>
                </div>
              </div>
              <div aria-label="Course dashboard on a laptop and phone" className="device-preview">
                <div className="laptop-preview">
                  <div className="preview-toolbar"><span>comcode</span><span>My learning</span><span>●</span></div>
                  <div className="preview-content">
                    <span className="preview-kicker">YOUR COURSE</span>
                    <strong>Data Structures</strong>
                    <span className="preview-subtitle">A little progress, every day.</span>
                    <div className="preview-progress"><span /></div>
                    <div className="preview-lesson"><i>✓</i><span>Arrays &amp; complexity</span><b>Done</b></div>
                    <div className="preview-lesson preview-current"><i>→</i><span>Linked lists</span><b>Next</b></div>
                  </div>
                  <div className="laptop-base" />
                </div>
                <div className="phone-preview">
                  <div className="phone-camera" />
                  <div className="phone-screen">
                    <span className="phone-greeting">GOOD AFTERNOON</span>
                    <strong>Keep it going.</strong>
                    <div className="phone-course">
                      <span>CONTINUE LEARNING</span>
                      <b>Data Structures</b>
                      <small>Linked lists · 8 min</small>
                      <i>Resume lesson &nbsp;→</i>
                    </div>
                    <div className="phone-streak"><span>✳</span> You&apos;re building a study habit.</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="architecture-panel">
              <div className="architecture-heading">
                <span className="architecture-kicker">A SHARED TECHNICAL FOUNDATION</span>
                <span>Proposed architecture</span>
              </div>
              <div className="architecture-grid">
                {architecture.map((item) => (
                  <div className="architecture-item" key={item.label}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </div>
                ))}
              </div>
              <p>
                One API and course library serve the website and mobile apps,
                with secure accounts and permissions designed in from the start.
              </p>
            </div>
          </div>
        </section>

        <section
          aria-labelledby="roadmap-title"
          className="roadmap-section"
          id="roadmap"
        >
          <div className="page-shell">
            <div className="roadmap-heading">
              <div className="eyebrow">From first sketch to a working product</div>
              <h2 id="roadmap-title">
                A thoughtful plan
                <br />
                <span>for building ComCode.</span>
              </h2>
              <p>
                Build the essentials first, then bring the learning experience
                together across web and mobile.
              </p>
            </div>
            <ol className="roadmap-grid">
              {buildPhases.map((phase) => (
                <li className="roadmap-card" key={phase.number}>
                  <span className="roadmap-number">{phase.number}</span>
                  <h3>{phase.title}</h3>
                  <p>{phase.description}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section aria-labelledby="plans-title" className="plans-section page-shell" id="plans">
          <div className="plans-heading">
            <div className="eyebrow">A plan that fits your pace</div>
            <h2 id="plans-title">Keep learning, <span>your way.</span></h2>
            <p>Start small or commit to the long view. Your next step is yours to choose.</p>
          </div>
          <div className="plans-grid">
            {plans.map((plan) => (
              <article className={`plan-card${plan.featured ? " plan-featured" : ""}`} key={plan.name}>
                <div className="plan-card-top">
                  <h3>{plan.name}</h3>
                  {plan.featured && <span className="best-value">BEST VALUE</span>}
                </div>
                <span className="plan-detail">{plan.detail}</span>
                <div className="plan-price">
                  <strong>{plan.price}</strong>
                  <span>{plan.billingPeriod}</span>
                </div>
                <p>{plan.description}</p>
                <a className={plan.featured ? "plan-link plan-link-featured" : "plan-link"} href={`/checkout?plan=${plan.id}`}>
                  Choose {plan.name.toLowerCase()} <ArrowIcon />
                </a>
              </article>
            ))}
          </div>
          <div className="billing-methods">
            <div className="billing-method">
              <span className="billing-brand paystack-brand">P</span>
              <span><strong>Paystack</strong><small>Cards with automatic renewals</small></span>
            </div>
            <span className="billing-method-divider" />
            <div className="billing-method">
              <span className="billing-brand mpesa-brand">M</span>
              <span><strong>M-Pesa · Daraja</strong><small>Approve each renewal on your phone</small></span>
            </div>
          </div>
          <p className="plans-note">Secure hosted checkout. M-Pesa renewals always require your approval.</p>
        </section>
      </main>

      <footer className="site-footer">
        <div className="footer-main page-shell">
          <div className="footer-brand">
            <a aria-label="ComCode home" className="brand brand-footer" href="#">
              <span aria-hidden="true" className="brand-mark">c</span>
              <span>comcode</span>
            </a>
            <p>A more thoughtful way to learn computer science.</p>
          </div>
          <div className="footer-links">
            <div><span>LEARN</span><a href="#curriculum">Curriculum</a><a href="#lesson">Sample lesson</a><a href="#platform">Platform</a></div>
            <div><span>COMCODE</span><a href="#roadmap">Our roadmap</a><a href="#plans">Plans</a><a href="#start">Get started</a></div>
          </div>
        </div>
        <div className="footer-bottom page-shell">
          <span>© 2026 ComCode. Learn deeply. Build confidently.</span>
          <span>Made for curious minds, everywhere.</span>
        </div>
      </footer>
    </>
  );
}
