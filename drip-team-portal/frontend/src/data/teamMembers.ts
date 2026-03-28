import { TeamMember } from '../types/TeamMember';

export const teamMembers: TeamMember[] = [
  {
    id: 'lead',
    slug: 'jamie-marwell',
    name: 'Jamie Marwell',
    role: 'Lead Engineer',
    field: 'Mechanical & Systems Design',
    description: 'Leading the development of DRIP\'s acoustic deposition manufacturing system. Responsible for overall system architecture, mechanical design, and cross-disciplinary integration.',
    imageUrl: '/team-images/jamie-marwell.jpg',
    linkedinUrl: 'https://www.linkedin.com/in/james-marwell-90555b1b1/'
  },
  {
    id: 'chemical',
    slug: 'emma-blemaster',
    name: 'Emma Blemaster',
    role: 'Chemical',
    field: 'Materials & Chemical Processes',
    description: 'Developing material processing and chemical formulations for DRIP\'s acoustic deposition manufacturing system.',
    imageUrl: '/team-images/emma-blemaster.jpg',
    linkedinUrl: 'https://www.linkedin.com/in/emma-belle-blemaster-4634092a1/'
  },
  {
    id: 'software',
    slug: 'addison-prarie',
    name: 'Addison Prarie',
    role: 'Software/Simulation',
    field: 'Computational Modeling & Software',
    description: 'Building control software and computational simulations for DRIP\'s acoustic deposition manufacturing system.',
    imageUrl: '/team-images/addison-prarie.jpg'
  },
  {
    id: 'acoustics',
    slug: 'ryota-sato',
    name: 'Ryota Sato',
    role: 'Acoustics',
    field: 'Acoustic Systems & Signal Processing',
    description: 'Designing the acoustic phased array and signal processing systems that enable contact-free metal deposition at DRIP.',
    imageUrl: '/team-images/ryota-sato.jpg',
    linkedinUrl: 'https://www.linkedin.com/in/ryos17/'
  },
  {
    id: 'electrical',
    slug: 'molly-miller',
    name: 'Molly Miller',
    role: 'Power Systems',
    field: 'PCB Design & Power Architecture',
    description: 'Building power electronics and PCB systems for DRIP\'s acoustic deposition manufacturing platform.',
    imageUrl: '/team-images/molly-miller.jpg',
    linkedinUrl: 'https://www.linkedin.com/in/molly-o-miller/'
  },
  {
    id: 'mechanical',
    slug: 'pierce-thompson',
    name: 'Pierce Thompson',
    role: 'Mechanical',
    field: 'Aerospace & Mechanical Systems',
    description: 'Designing structural and mechanical systems for DRIP\'s acoustic deposition manufacturing platform.',
    imageUrl: '/team-images/pierce-thompson.jpg'
  }
];