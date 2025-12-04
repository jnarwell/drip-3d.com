export interface TeamMember {
  id: string;
  name: string;
  role: string;
  field: string;
  imageUrl: string;
  // Future Linear integration fields
  leadProjects?: string[];
  bio?: string;
  email?: string;
  linkedinUrl?: string;
}