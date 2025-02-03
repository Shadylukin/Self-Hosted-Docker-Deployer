# Pirate Mode Guide

This guide explains how to use the Pirate mode feature to set up a complete media automation environment.

## Overview

Pirate mode automatically deploys a curated collection of services designed to work together for media automation:

- Media Server: Stream and organize your media collection
- Content Aggregator: Discover and organize content
- Download Manager: Automate downloads

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

### Media Server
- Purpose: Stream and organize your media collection
- Default port: 8096
- Web interface: http://localhost:8096
- Default paths:
  - Config: `<media-path>/config`
  - Media: `<media-path>/media`

### Content Aggregator
- Purpose: Discover and organize content
- Default port: 8989
- Web interface: http://localhost:8989
- Default paths:
  - Config: `<media-path>/config`
  - Downloads: `<media-path>/downloads`
  - Media: `<media-path>/media`

### Download Manager
- Purpose: Automate downloads
- Default port: 8080
- Web interface: http://localhost:8080
- Default paths:
  - Config: `<media-path>/config`
  - Downloads: `<media-path>/downloads`

## Initial Setup

1. After deployment, access each service through its web interface
2. Complete the initial setup wizards for each service
3. Configure the Content Aggregator to use the Download Manager:
   - In Content Aggregator settings, add a new download client
   - Use "download-manager" as the hostname
   - Use the default port 8080

## Automation Setup

### Content Organization

1. In the Content Aggregator:
   - Add your preferred content sources
   - Configure quality preferences
   - Set up naming conventions
   - Configure download path: `/downloads`
   - Configure media path: `/media`

### Download Automation

1. In the Download Manager:
   - Configure download speed limits if needed
   - Set up categories for different content types
   - Configure the default save path to `/downloads`

### Media Library

1. In the Media Server:
   - Add `/media` as your library path
   - Configure library types (Movies, TV Shows, etc.)
   - Set up metadata agents
   - Configure auto-scan of new content

## Troubleshooting

### Common Issues

1. **Services can't communicate**
   - Ensure all services are on the `pirate_network`
   - Check that service names are used as hostnames

2. **Download issues**
   - Verify path mappings in Content Aggregator
   - Check Download Manager categories
   - Ensure proper permissions on media directories

3. **Media not appearing**
   - Check file permissions
   - Verify path mappings
   - Force a library scan in Media Server

### Logs

To view service logs:

```bash
docker-compose logs -f [service-name]
```

Replace [service-name] with:
- media-server
- content-aggregator
- download-manager

## Security Considerations

1. **Network Security**
   - All services are configured to only be accessible locally
   - Use a VPN or reverse proxy for remote access
   - Change default passwords immediately

2. **Storage**
   - Regular backups of the config directory are recommended
   - Monitor disk space usage
   - Set up disk space alerts

## Updating

Services will automatically update to the latest version when restarted:

```bash
docker-compose pull
docker-compose up -d
```

## Additional Resources

- [Media Server Documentation](https://jellyfin.org/docs)
- [Content Aggregator Guide](https://wiki.servarr.com)
- [Download Manager Manual](https://github.com/qbittorrent/qBittorrent/wiki)

## Legal Considerations

This tool is designed for managing your personal media collection. Always ensure you have the right to access and store any content you manage with these tools. 