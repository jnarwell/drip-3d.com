import React from 'react';
import { TeamMember } from '../../types/TeamMember';
import { useFadeInWhenVisible } from '../../hooks/useFadeInWhenVisible';

interface TeamMemberCardProps {
  member: TeamMember;
  onClick?: () => void;
}

const TeamMemberCard: React.FC<TeamMemberCardProps> = ({ member, onClick }) => {
  const fadeIn = useFadeInWhenVisible();

  return (
    <div 
      ref={fadeIn.ref}
      onClick={onClick}
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        overflow: 'hidden',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        opacity: fadeIn.isVisible ? 1 : 0,
        transition: 'opacity 0.4s ease-in-out, transform 0.2s ease',
        cursor: onClick ? 'pointer' : 'default',
        transform: 'translateY(0)'
      }}
      onMouseEnter={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(-4px)';
          e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
        }
      }}
      onMouseLeave={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        }
      }}
    >
      {/* Image with title banner */}
      <div style={{ position: 'relative', paddingBottom: '100%', backgroundColor: '#ebf0f1' }}>
        <img 
          src={member.imageUrl}
          alt={member.name}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center top'
          }}
          onError={(e) => {
            // Fallback for missing images - show initials
            const parent = e.currentTarget.parentElement;
            if (parent) {
              e.currentTarget.style.display = 'none';
              const initials = member.name.split(' ').map(n => n[0]).join('');
              const initialsDiv = document.createElement('div');
              initialsDiv.style.cssText = 'position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; font-size: 48px; font-weight: bold; color: #354857;';
              initialsDiv.textContent = initials;
              parent.appendChild(initialsDiv);
            }
          }}
        />
        {/* Role banner */}
        <div style={{
          position: 'absolute',
          bottom: '10px',
          left: 0,
          right: 0,
          backgroundColor: 'rgba(53, 72, 87, 0.9)',
          color: '#ffffff',
          padding: '10px 20px',
          fontSize: '14px',
          fontWeight: '600',
          textAlign: 'center'
        }}>
          {member.role}
        </div>
      </div>
      
      {/* Card content */}
      <div style={{ padding: '20px' }}>
        <h3 style={{
          color: '#354857',
          fontSize: '24px',
          fontWeight: 'bold',
          marginBottom: '8px'
        }}>
          {member.name}
        </h3>
        <p style={{
          color: '#666666',
          fontSize: '16px',
          margin: 0
        }}>
          {member.field}
        </p>
      </div>
    </div>
  );
};

export default TeamMemberCard;