"""
Script for generating matplotlib markers from svg files for indicating sun and moon on forecast plots.
"""
if __name__ == "__main__":

    import matplotlib as mpl
    from svgpathtools import svg2paths
    from svgpath2mpl import parse_path
    import pickle


    def generate_marker_from_svg(svg_path):
        image_path, attributes = svg2paths(svg_path)
        image_marker = parse_path(attributes[0]['d'])
        image_marker.vertices -= image_marker.vertices.mean(axis=0)
        image_marker = image_marker.transformed(mpl.transforms.Affine2D().rotate_deg(180))
        image_marker = image_marker.transformed(mpl.transforms.Affine2D().scale(-1, 1))
        return image_marker


    moon_svgs = {'Full Moon': 'moon-full.svg',
                 'New Moon': 'moon-new.svg',
                 'First Quarter': 'moon-first-quarter.svg',
                 'Third Quarter': 'moon-last-quarter.svg',
                 'Waxing Crescent': 'moon-waxing-crescent.svg',
                 'Waxing Gibbous': 'moon-waxing-gibbous.svg',
                 'Waning Crescent': 'moon-waning-crescent.svg',
                 'Waning Gibbous': 'moon-waning-gibbous.svg'}

    # generate mpl markers from svg images
    icons_dir = './icons'
    import os
    moon_icons = {}
    for phase, moon_icon in moon_svgs.items():
        marker = generate_marker_from_svg(os.path.join(icons_dir, moon_icon))
        moon_icons[phase] = marker
    pickle.dump(moon_icons, open('./icons/moon_markers.obj', 'wb'))
    sun_icon = generate_marker_from_svg(os.path.join(icons_dir, 'sun.svg'))
    pickle.dump(sun_icon, open('./icons/sun_marker.obj', 'wb'))
