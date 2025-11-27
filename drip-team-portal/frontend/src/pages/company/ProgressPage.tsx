import React, { useEffect } from 'react';

const ProgressPage: React.FC = () => {
  useEffect(() => {
    // Initialize animations
    const initScrollAnimations = () => {
      const observerOptions = {
        threshold: 0.2,
        rootMargin: '0px 0px -100px 0px'
      };

      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('active');
          }
        });
      }, observerOptions);

      const animatedElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
      animatedElements.forEach(el => observer.observe(el));
    };

    initScrollAnimations();
  }, []);

  return (
    <>
      {/* Header */}
      <header className="site-header">
        <div className="container">
          <div className="site-header__inner">
            <div className="logo">
              <a href="/">DRIP</a>
            </div>
            <nav className="main-nav">
              <ul>
                <li><a href="/">Home</a></li>
                <li><a href="/progress" className="active">Progress</a></li>
                <li><a href="/team">Team</a></li>
              </ul>
            </nav>
            <button className="mobile-menu-toggle" aria-label="Toggle menu">☰</button>
          </div>
        </div>
      </header>

      {/* Progress Hero */}
      <section className="progress-hero">
        <div className="container container--content text-center">
          <h1 className="animate-fade-in-down">Development Progress</h1>
          <p className="text-lg mt-lg animate-fade-in-up">Building the future of acoustic deposition manufacturing</p>
        </div>
      </section>

      {/* Phase Checklist */}
      <section className="section">
        <div className="container">
          <div className="phase-checklist">
            <h2 className="text-center mb-xl">Project Phases</h2>
            
            {/* Phase 1 */}
            <div className="phase reveal" data-phase="1">
              <div className="phase__header">
                <div className="phase__title">
                  <span className="phase__icon">1</span>
                  <span>Phase 1: Design & Planning</span>
                </div>
                <div className="phase__date">Aug 27, 2025 - Jan 30, 2026</div>
              </div>
              <div className="phase__content">
                <div className="phase__milestones">
                  <div className="milestone milestone--complete">
                    <h4>Requirements Definition</h4>
                    <p>Completed SR001-SR015 system requirements documentation</p>
                  </div>
                  <div className="milestone milestone--complete">
                    <h4>System Architecture</h4>
                    <p>Finalized modular architecture with 9 subsystems</p>
                  </div>
                  <div className="milestone">
                    <h4>Component Selection</h4>
                    <p>Select ultrasonic transducers, power systems, and control hardware</p>
                  </div>
                  <div className="milestone">
                    <h4>CAD Design</h4>
                    <p>Complete preliminary CAD models for all subsystems</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Phase 2 */}
            <div className="phase reveal" data-phase="2">
              <div className="phase__header">
                <div className="phase__title">
                  <span className="phase__icon">2</span>
                  <span>Phase 2: Validation</span>
                </div>
                <div className="phase__date">Oct 12, 2025 - Feb 28, 2026</div>
              </div>
              <div className="phase__content">
                <div className="phase__milestones">
                  <div className="milestone">
                    <h4>Particle Steering</h4>
                    <p>Demonstrate acoustic steering with styrofoam particles</p>
                  </div>
                  <div className="milestone">
                    <h4>Liquid Metal Steering</h4>
                    <p>Control gallium-indium droplets using acoustic field</p>
                  </div>
                  <div className="milestone">
                    <h4>Aluminum Testing</h4>
                    <p>Initial tests with molten aluminum droplets</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Phase 3 */}
            <div className="phase reveal" data-phase="3">
              <div className="phase__header">
                <div className="phase__title">
                  <span className="phase__icon">3</span>
                  <span>Phase 3: Procurement</span>
                </div>
                <div className="phase__date">Mar 1 - Apr 26, 2026</div>
              </div>
              <div className="phase__content">
                <div className="phase__milestones">
                  <div className="milestone">
                    <h4>Ultrasonic Components</h4>
                    <p>Order ultrasonic transducers for acoustic array</p>
                  </div>
                  <div className="milestone">
                    <h4>Power Electronics</h4>
                    <p>Acquire MESA induction heater and DC power supplies</p>
                  </div>
                  <div className="milestone">
                    <h4>Control Systems</h4>
                    <p>Purchase NI DAQ, Arduino controllers, and interface boards</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Phase 4 */}
            <div className="phase reveal" data-phase="4">
              <div className="phase__header">
                <div className="phase__title">
                  <span className="phase__icon">4</span>
                  <span>Phase 4: Integration</span>
                </div>
                <div className="phase__date">Mar 1 - May 10, 2026</div>
              </div>
              <div className="phase__content">
                <div className="phase__milestones">
                  <div className="milestone">
                    <h4>Subsystem Assembly</h4>
                    <p>Assemble and test individual subsystems</p>
                  </div>
                  <div className="milestone">
                    <h4>System Integration</h4>
                    <p>Integrate all subsystems per ICDs</p>
                  </div>
                  <div className="milestone">
                    <h4>Software Development</h4>
                    <p>Implement control algorithms and user interface</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Phase 5 */}
            <div className="phase reveal" data-phase="5">
              <div className="phase__header">
                <div className="phase__title">
                  <span className="phase__icon">5</span>
                  <span>Phase 5: Verification</span>
                </div>
                <div className="phase__date">May 11 - Jun 7, 2026</div>
              </div>
              <div className="phase__content">
                <div className="phase__milestones">
                  <div className="milestone">
                    <h4>Performance Testing</h4>
                    <p>Validate all system requirements</p>
                  </div>
                  <div className="milestone">
                    <h4>Material Studies</h4>
                    <p>Test with aluminum, steel, and exotic alloys</p>
                  </div>
                  <div className="milestone">
                    <h4>Optimization</h4>
                    <p>Refine control algorithms and improve performance</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Upcoming Milestones */}
      <section className="section">
        <div className="container container--content">
          <h2 className="text-center mb-xl">Upcoming Milestones</h2>
          <div className="grid grid--1">
            <div className="milestone-card reveal">
              <div className="milestone-card__date">December 1, 2025</div>
              <h3>Particle Steering Demonstration</h3>
              <p>Demonstrate acoustic control of styrofoam particles</p>
            </div>
            
            <div className="milestone-card reveal">
              <div className="milestone-card__date">January 15, 2026</div>
              <h3>Liquid Metal Testing</h3>
              <p>Control gallium-indium droplets using acoustic field</p>
            </div>
            
            <div className="milestone-card reveal">
              <div className="milestone-card__date">February 28, 2026</div>
              <h3>Aluminum Testing</h3>
              <p>Initial tests with molten aluminum droplets</p>
            </div>
          </div>
          
          <div className="text-center mt-xl">
            <p className="text-sm text-muted">Last updated: August 27, 2025</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="site-footer">
        <div className="container">
          <div className="footer__content">
            <div className="footer__section">
              <h4>Project</h4>
              <a href="/">Home</a>
              <a href="/progress">Development Progress</a>
              <a href="/team">Team</a>
            </div>
            <div className="footer__section">
              <h4>Contact</h4>
              <p className="text-sm">Email: <a href="mailto:jamie@drip-3d.com" style={{display: 'inline'}}>jamie@drip-3d.com</a><br/>
              Primary Contact: Jamie Marwell</p>
            </div>
          </div>
          <div className="footer__bottom">
            <p>&copy; 2025 Drip 3D Inc. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </>
  );
};

export default ProgressPage;