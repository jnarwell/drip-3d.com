import React from 'react';
import { useParams, Navigate, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Navigation from '../../components/company/Navigation';
import Footer from '../../components/company/Footer';
import { useBodyBackground } from './useBodyBackground';
import { useMobile } from '../../hooks/useMobile';
import { teamMembers } from '../../data/teamMembers';

const LinkedInIcon: React.FC = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
  </svg>
);

const TeamMemberProfile: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const isMobile = useMobile();
  useBodyBackground('#ebf0f1');

  const member = teamMembers.find((m) => m.slug === slug);

  if (!member) {
    return <Navigate to="/team" />;
  }

  const ogImageUrl = `https://drip-3d.com${member.imageUrl}`;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#ebf0f1' }}>
      <Helmet>
        <title>{member.name} - DRIP</title>
        <meta name="description" content={`${member.role} at DRIP. ${member.description}`} />
        <meta property="og:title" content={`${member.name} - ${member.role} at DRIP`} />
        <meta property="og:description" content={member.description} />
        <meta property="og:type" content="profile" />
        <meta property="og:url" content={`https://drip-3d.com/team/${member.slug}`} />
        <meta property="og:image" content={ogImageUrl} />
        <meta name="twitter:card" content="summary" />
        <meta name="twitter:title" content={`${member.name} - ${member.role} at DRIP`} />
        <meta name="twitter:description" content={member.description} />
        <meta name="twitter:image" content={ogImageUrl} />
      </Helmet>

      <Navigation activePage="team" />

      <main style={{
        maxWidth: '600px',
        margin: '0 auto',
        padding: isMobile ? '40px 20px 80px' : '60px 24px 80px'
      }}>
        <Link
          to="/team"
          style={{
            display: 'inline-block',
            marginBottom: '24px',
            color: '#666',
            textDecoration: 'none',
            fontSize: '0.875rem'
          }}
        >
          &larr; Back to Team
        </Link>

        <img
          src={member.imageUrl}
          alt={member.name}
          style={{
            width: '120px',
            height: '120px',
            borderRadius: '50%',
            objectFit: 'cover',
            marginBottom: '24px',
            display: 'block'
          }}
        />

        <h1 style={{
          fontSize: '2rem',
          fontWeight: 700,
          color: '#354857',
          marginBottom: '4px'
        }}>
          {member.name}
        </h1>

        <p style={{
          color: '#354857',
          fontWeight: 500,
          marginBottom: '16px',
          opacity: 0.8
        }}>
          {member.role} &middot; {member.field}
        </p>

        <p style={{
          color: '#666',
          lineHeight: 1.6,
          marginBottom: '24px'
        }}>
          {member.description}
        </p>

        {member.linkedinUrl && (
          <a
            href={member.linkedinUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              color: '#0077b5',
              textDecoration: 'none',
              fontWeight: 500
            }}
          >
            <LinkedInIcon />
            LinkedIn
          </a>
        )}
      </main>

      <Footer />
    </div>
  );
};

export default TeamMemberProfile;
