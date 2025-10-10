# DRIP-3D.com Website

Professional showcase website for the DRIP (Droplet Refractory In-flight Printing) acoustic levitation manufacturing system.

## Overview

This is a static website built for the DRIP project at Stanford University. The site serves as a professional showcase for the acoustic levitation manufacturing system, targeting Stanford students/faculty and potential investors.

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Design System**: Custom CSS with industrial/metal aesthetic
- **Fonts**: Inter, JetBrains Mono
- **Icons**: Custom SVG icons
- **Data**: JSON files for dynamic content
- **Hosting**: GitHub Pages / Vercel (ready for deployment)

## Project Structure

```
drip-3d.com/
├── index.html              # Home page
├── progress.html           # Development progress
├── team.html              # Team & recruitment
├── assets/
│   ├── css/               # Stylesheets
│   │   ├── reset.css      # CSS reset
│   │   ├── variables.css  # Design tokens
│   │   ├── layout.css     # Grid system
│   │   ├── components.css # UI components
│   │   ├── pages.css      # Page styles
│   │   └── animations.css # Animations
│   ├── js/                # JavaScript
│   │   ├── main.js        # Core utilities
│   │   ├── navigation.js  # Header/nav
│   │   ├── progress.js    # Progress page
│   │   ├── team.js        # Team modals
│   │   └── forms.js       # Form handling
│   └── images/            # Image assets
├── data/                  # JSON data
│   ├── specs.json         # System specs
│   ├── milestones.json    # Progress data
│   └── team.json          # Team info
└── README.md              # This file
```

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/jnarwell/drip-3d.com.git
cd drip-3d.com
```

2. Install live server (optional):
```bash
npm install -g live-server
```

3. Start local server:
```bash
live-server --port=3000
```

4. Open browser to `http://localhost:3000`

## Deployment

### GitHub Pages

1. Push to GitHub repository
2. Go to Settings > Pages
3. Select source branch (main)
4. Site will be available at `https://[username].github.io/drip-3d.com/`

### Vercel

1. Import project to Vercel
2. No build configuration needed (static site)
3. Deploy

## Content Management

### Updating Progress

Edit `data/milestones.json`:
- Update phase progress percentages
- Add new milestones
- Mark milestones as complete
- Update subsystem progress

### Adding Team Members

Edit `data/team.json`:
- Add member objects to `current` array
- Include photo path, bio, and social links
- Update open positions as needed

### Modifying System Specs

Edit `data/specs.json`:
- Update system specifications
- Add new capability data
- Modify level comparisons

## Design System

### Colors
- Primary: Steel Dark (#2C3E50)
- Accent: Acoustic Blue (#3498DB)
- Alert: Thermal Orange (#E67E22)
- Background: Ceramic White (#ECF0F1)

### Typography
- Headers: Inter 600
- Body: Inter 400
- Code: JetBrains Mono

### Breakpoints
- Mobile: < 768px
- Tablet: 768px - 1023px
- Desktop: ≥ 1024px

## Performance

- All images optimized (< 200KB)
- CSS/JS minified for production
- Lazy loading for images
- Smooth scroll animations
- Responsive design

## Browser Support

- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions  
- Safari: Last 2 versions
- Mobile: iOS 13+, Android 10+

## Contributing

1. Create feature branch
2. Make changes
3. Test responsiveness
4. Submit pull request

## License

© 2025 DRIP Acoustic Manufacturing. All rights reserved.

## Contact

- Project Documentation: https://jnarwell.github.io/drip
- GitHub: https://github.com/jnarwell/drip
- Email: drip-team@stanford.edu