export interface TeamMember {
  id: string;
  slug: string;
  name: string;
  role: string;
  field: string;
  description: string;
  imageUrl: string;
  linkedinUrl?: string;
  // Future Linear integration fields
  leadProjects?: string[];
  bio?: string;
  email?: string;
}