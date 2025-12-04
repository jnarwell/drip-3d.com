import React, { useState } from 'react';
import Navigation from '../../components/company/Navigation';
import Footer from '../../components/company/Footer';
import { useFadeInWhenVisible } from '../../hooks/useFadeInWhenVisible';
import { useBodyBackground } from './useBodyBackground';
import { useLinearProgress } from '../../hooks/useLinearData';

const ProgressPage: React.FC = () => {
  // Set body background to match top section
  useBodyBackground('#354857');
  
  const section1Content = useFadeInWhenVisible();
  const section2 = useFadeInWhenVisible();
  const section3 = useFadeInWhenVisible();
  
  const { phases, loading, error } = useLinearProgress();
  const [expandedPhases, setExpandedPhases] = useState<Set<number>>(new Set());

  const togglePhase = (phaseNumber: number) => {
    setExpandedPhases(prev => {
      const newSet = new Set(prev);
      if (newSet.has(phaseNumber)) {
        newSet.delete(phaseNumber);
      } else {
        newSet.add(phaseNumber);
      }
      return newSet;
    });
  };

  const formatPhaseName = (fullName: string) => {
    // Remove "Phase X - " from the beginning
    return fullName.replace(/^Phase \d+ - /, '');
  };

  const calculatePhaseProgress = (phase: any) => {
    if (!phase.projects || phase.projects.length === 0) {
      return 0;
    }
    
    const totalProgress = phase.projects.reduce((sum: number, project: any) => {
      // Convert decimal progress to percentage
      const projectProgress = project.progress * 100;
      return sum + projectProgress;
    }, 0);
    
    return Math.round(totalProgress / phase.projects.length);
  };

  return (
    <div style={{ 
      minHeight: '100vh'
    }}>
      {/* Navigation */}
      <Navigation activePage="progress" />
      
      {/* Section 1 - Gray Background */}
      <section style={{ 
        backgroundColor: '#ebf0f1',
        padding: '60px 42px'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h1 style={{ 
            color: '#354857',
            marginBottom: '40px',
            fontSize: '48px',
            fontWeight: 'bold',
            textAlign: 'center'
          }}>
            Development Progress
          </h1>
          
          {/* Progress content */}
          <div 
            ref={section1Content.ref}
            style={{ 
              marginTop: '40px',
              opacity: section1Content.isVisible ? 1 : 0,
              transition: 'opacity 0.4s ease-in-out'
            }}>
            {loading && (
              <p style={{ color: '#666666', fontSize: '18px', textAlign: 'center' }}>
                Loading progress data...
              </p>
            )}
            
            {error && (
              <p style={{ color: '#666666', fontSize: '18px', textAlign: 'center' }}>
                Error loading progress data
              </p>
            )}
            
            {!loading && !error && phases.length === 0 && (
              <p style={{ color: '#666666', fontSize: '18px', textAlign: 'center' }}>
                No phases found
              </p>
            )}
            
            {!loading && !error && phases.map(phase => (
              <div
                key={phase.phase}
                style={{
                  marginBottom: '12px',
                  backgroundColor: '#ffffff',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}
              >
                {/* Phase Header */}
                <button
                  onClick={() => togglePhase(phase.phase)}
                  style={{
                    width: '100%',
                    padding: '20px 24px',
                    backgroundColor: '#ffffff',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'background-color 0.2s ease',
                    fontFamily: 'inherit'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f8f9fa';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#ffffff';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{
                      width: '35px',
                      height: '35px',
                      borderRadius: '50%',
                      backgroundColor: '#354857',
                      color: '#ffffff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '18px',
                      fontWeight: 'bold'
                    }}>
                      {phase.phase}
                    </div>
                    <span style={{
                      fontSize: '20px',
                      color: '#354857'
                    }}>
                      {formatPhaseName(phase.title)}
                    </span>
                  </div>
                  
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span style={{
                      fontSize: '16px',
                      color: '#666666'
                    }}>
                      {phase.targetDate}
                    </span>
                    <svg
                      style={{
                        width: '24px',
                        height: '24px',
                        transform: expandedPhases.has(phase.phase) ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.3s ease',
                        fill: '#666666'
                      }}
                      viewBox="0 0 24 24"
                    >
                      <path d="M7 10l5 5 5-5z"/>
                    </svg>
                  </div>
                </button>
                
                {/* Expandable Content */}
                {expandedPhases.has(phase.phase) && (
                  <div style={{
                    padding: '24px',
                    backgroundColor: '#f8f9fa',
                    borderTop: '1px solid #e9ecef'
                  }}>
                    {phase.description && (
                      <p style={{ 
                        color: '#666666', 
                        fontSize: '16px',
                        fontStyle: 'italic',
                        textAlign: 'center',
                        margin: '0 0 24px 0',
                        lineHeight: '1.6'
                      }}>
                        {phase.description}
                      </p>
                    )}
                    
                    {phase.projects && phase.projects.length > 0 && (
                      <>
                        {/* Progress bar */}
                        <div style={{
                          marginBottom: '24px'
                        }}>
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            marginBottom: '8px',
                            fontSize: '14px',
                            color: '#666666'
                          }}>
                            <span>Overall Progress</span>
                            <span>{calculatePhaseProgress(phase)}%</span>
                          </div>
                          <div style={{
                            width: '100%',
                            height: '12px',
                            backgroundColor: '#e9ecef',
                            borderRadius: '6px',
                            overflow: 'hidden'
                          }}>
                            <div style={{
                              width: `${calculatePhaseProgress(phase)}%`,
                              height: '100%',
                              backgroundColor: '#354857',
                              borderRadius: '6px',
                              transition: 'width 0.3s ease'
                            }} />
                          </div>
                        </div>
                        
                        {/* Projects section */}
                        <div>
                          <h3 style={{
                            color: '#354857',
                            fontSize: '18px',
                            fontWeight: 'bold',
                            marginBottom: '16px'
                          }}>
                            Projects:
                          </h3>
                          
                          <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '16px'
                          }}>
                            {phase.projects
                              .sort((a: any, b: any) => {
                                // Sort by targetDate, handling "TBD" and missing dates
                                if (!a.targetDate || a.targetDate === "TBD") return 1;
                                if (!b.targetDate || b.targetDate === "TBD") return -1;
                                
                                // Parse dates for comparison
                                const dateA = new Date(a.targetDate);
                                const dateB = new Date(b.targetDate);
                                
                                return dateA.getTime() - dateB.getTime();
                              })
                              .map((project: any) => (
                              <div
                                key={project.id}
                                style={{
                                  backgroundColor: '#ffffff',
                                  borderRadius: '8px',
                                  padding: '20px',
                                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                                }}
                              >
                                <h4 style={{
                                  color: '#354857',
                                  fontSize: '16px',
                                  fontWeight: '600',
                                  marginBottom: '8px'
                                }}>
                                  {project.name}
                                </h4>
                                
                                {project.description && (
                                  <p style={{
                                    color: '#666666',
                                    fontSize: '14px',
                                    marginBottom: '16px',
                                    lineHeight: '1.5'
                                  }}>
                                    {project.description}
                                  </p>
                                )}
                                
                                {/* Project progress bar */}
                                <div>
                                  <div style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    marginBottom: '6px',
                                    fontSize: '13px',
                                    color: '#666666'
                                  }}>
                                    <span>Progress</span>
                                    <span>{Math.round(project.progress * 100)}%</span>
                                  </div>
                                  <div style={{
                                    width: '100%',
                                    height: '8px',
                                    backgroundColor: '#e9ecef',
                                    borderRadius: '4px',
                                    overflow: 'hidden'
                                  }}>
                                    <div style={{
                                      width: `${Math.round(project.progress * 100)}%`,
                                      height: '100%',
                                      backgroundColor: '#354857',
                                      borderRadius: '4px',
                                      transition: 'width 0.3s ease'
                                    }} />
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default ProgressPage;