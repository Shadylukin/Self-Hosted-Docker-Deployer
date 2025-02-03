# 🏴‍☠️ Pirate Mode Guide

This guide explains how to use the Pirate mode feature to set up a complete media automation environment.

## Overview

Pirate mode automatically deploys a curated collection of services designed to work together for media automation:

- **Plex**: Stream and organize your media collection
- **Overseerr**: Request and discover new content
- **Sonarr**: Automate TV show downloads and management
- **Radarr**: Automate movie downloads and management
- **Prowlarr**: Manage and coordinate indexers
- **qBittorrent**: Handle downloads with a web interface

## Quick Start

To deploy all services with default settings:

```bash
easy-docker-deploy pirate
```

This will:
1. Create default directories for media storage
2. Deploy all required services
3. Configure them to work together
4. Set up a private network for inter-service communication

## Custom Configuration

### Media Storage Location

By default, media is stored in `~/media`. To use a different location:

```bash
easy-docker-deploy pirate --media-path /path/to/media
```

The following subdirectories will be created:
- `/path/to/media/downloads`: For temporary download storage
- `/path/to/media/media`: For your organized media library
- `/path/to/media/config`: For service configurations

### Timezone Setting

Set your local timezone to ensure correct scheduling:

```bash
easy-docker-deploy pirate --timezone "America/New_York"
```

## Service Details

### Plex
- Purpose: Stream and organize your media collection
- Default port: 32400
- Web interface: http://localhost:32400/web
- Default paths:
  - Config: `<media-path>/config/plex`
  - Media: `<media-path>/media`

### Overseerr
- Purpose: Request and discover new content
- Default port: 5055
- Web interface: http://localhost:5055
- Default paths:
  - Config: `<media-path>/config/overseerr`

### Sonarr
- Purpose: TV show automation
- Default port: 8989
- Web interface: http://localhost:8989
- Default paths:
  - Config: `<media-path>/config/sonarr`
  - Downloads: `<media-path>/downloads`
  - Media: `<media-path>/media/tv`

### Radarr
- Purpose: Movie automation
- Default port: 7878
- Web interface: http://localhost:7878
- Default paths:
  - Config: `<media-path>/config/radarr`
  - Downloads: `<media-path>/downloads`
  - Media: `<media-path>/media/movies`

### Prowlarr
- Purpose: Indexer management
- Default port: 9696
- Web interface: http://localhost:9696
- Default paths:
  - Config: `<media-path>/config/prowlarr`

### qBittorrent
- Purpose: Download management
- Default port: 8080
- Web interface: http://localhost:8080
- Default credentials: admin/adminadmin
- Default paths:
  - Config: `<media-path>/config/qbittorrent`
  - Downloads: `<media-path>/downloads`

## Initial Setup

1. After deployment, access each service through its web interface
2. Complete the initial setup wizards for each service
3. Configure service integration:

### Prowlarr Setup
1. Add your preferred indexers
2. Configure Sonarr/Radarr integration:
   - Go to Settings -> Apps
   - Add Sonarr and Radarr applications
   - Use service names as hostnames (e.g., "sonarr", "radarr")

### Sonarr/Radarr Setup
1. Add qBittorrent as download client:
   - Host: qbittorrent
   - Port: 8080
   - Username: admin
   - Password: adminadmin
2. Configure media paths:
   - Downloads: /downloads
   - TV Shows (Sonarr): /media/tv
   - Movies (Radarr): /media/movies
3. Add Prowlarr as an indexer

### Overseerr Setup
1. Connect to Plex:
   - Use Plex claim token or sign in
2. Configure Sonarr/Radarr integration:
   - Add Sonarr and Radarr in settings
   - Use service names as hostnames
   - Use default ports

### Plex Setup
1. Access Plex web interface
2. Create libraries:
   - Movies: /media/movies
   - TV Shows: /media/tv
3. Configure scanning and metadata agents

## Troubleshooting

### Common Issues

1. **Services can't communicate**
   - Ensure all services are on the same Docker network
   - Check that service names are used as hostnames
   - Verify network settings in Docker

2. **Download issues**
   - Check qBittorrent connection in Sonarr/Radarr
   - Verify download path permissions
   - Test indexer connectivity in Prowlarr

3. **Media not appearing**
   - Check file permissions
   - Verify path mappings in all services
   - Ensure media follows naming conventions

4. **Port conflicts**
   - Check for other services using the same ports
   - Modify port mappings if needed
   - Ensure Docker host ports are available

## Security Considerations

1. **Change default passwords**
   - qBittorrent web interface
   - Any other service-specific credentials

2. **Network security**
   - Consider using a VPN for downloads
   - Restrict access to service UIs
   - Use secure passwords for all services

3. **File permissions**
   - Ensure proper PUID/PGID settings
   - Restrict access to media directories
   - Regular security audits

## Maintenance

1. **Regular updates**
   - Use Watchtower for automatic updates
   - Check for application-specific updates
   - Keep host system updated

2. **Backups**
   - Regular backup of config directories
   - Export important settings
   - Document any custom configurations

3. **Monitoring**
   - Check service logs regularly
   - Monitor disk space usage
   - Set up notifications for issues

## Additional Resources

- [Plex Documentation](https://support.plex.tv/articles/)
- [Sonarr Wiki](https://wiki.servarr.com/sonarr)
- [Radarr Wiki](https://wiki.servarr.com/radarr)
- [Prowlarr Wiki](https://wiki.servarr.com/prowlarr)
- [qBittorrent Documentation](https://github.com/qbittorrent/qBittorrent/wiki)
- [Overseerr Documentation](https://docs.overseerr.dev/) 