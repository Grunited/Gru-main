import spotipy
from spotipy.oauth2 import SpotifyOAuth
from assistants import Expert, STATUS_COMPLETED, STATUS_CONTINUE, STATUS_FAILURE
# from prompts import SPOTIFY_PROMPT
import dotenv
from typing import Optional, Dict, Any
import json
import time
import asyncio
# from poli_enum.country import Country

dotenv.load_dotenv()
    
NEWLINE_CHARACTER = '\n'

# class SpotifyExpert(Expert):
#     scope = "user-library-read playlist-modify-public"
#     def __init__(self, assistant_id: Optional[str]=None):
#         self.spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=self.scope))
#         super().__init__(tools=self.spotify_client, prompt=SPOTIFY_PROMPT, assistant_id=assistant_id)
        
#     def add_to_queue(self, uri: str) -> None:
#         """Adds a song to the user's Spotify queue.

#         Args:
#             uri (str): The ID of the song to add to the queue. Can be a Spotify URI, an ID, or a URL.
        
#         Returns:
#             None
#         """
#         self.spotify_client.add_to_queue(uri)
    
#     def album(self, album_id: str, market: Optional[Country]) -> Dict[str, Any]:
#         """Fetches an album from spotify according to `album_id`, which can be a Spotify URI, an album ID, or a URL, and `market`, which is an ISO 3166-1 alpha-2 country code.
        
#         Returns the corresponding Spotipy album object. Has the following properties:
#         `album_type`: str
#         `total_tracks`: int
#         `available_markets`: list
#         `external_urls`: dict
#         `href`: str
#         `id`: str
#         `images`: list
#         `name`: str
#         `release_date`: str
#         `release_date_precision`: str
#         `restrictions`: dict (only if `market` is not None)
#         `type`: str
#         `uri`: str
#         `artists`: list
#         `tracks`: list
#         `copyrights`: list
#         `external_ids`: dict
#         `genres`: list
#         `label`: str
#         `popularity`: int
        
#         Args:
#             album_id (str): The Spotify ID or URI or URL of the album.
#             market (str): An ISO 3166-1 alpha-2 country code to restrict results to or `None` to use the user's country.
        
#         Returns:
#             dict: The corresponding album object.
#         """
#         return self.spotify_client.album(album_id, market=market)

#     def album_tracks(album_id: str, limit=50, offset=0, market=None):
#         """Get Spotify catalog information about an album’s tracks. Optional parameters can be used to limit the number of tracks returned.
        
        
#         Returns the corresponding Spotipy response object. Contains the following properties:
#         `href`: str
#         `limit`: int
        
        
        
#         """

album_function = {
    "type": "function",
    "function": {
        "name": "album",
        "description": "Fetches an album from spotify according to `album_id`, which can be a Spotify URI, an album ID, or a URL, and `market`, which is an ISO 3166-1 alpha-2 country code.",
        "parameters": {
            "type": "object",
            "properties": {
                "album_id": {
                    "type": "string",
                    "description": "The Spotify ID or URI or URL of the album."
                },
                "market": {
                    "type": "string",
                    "description": "An ISO 3166-1 alpha-2 country code to restrict results to or `None` to use the user's country."
                }
            },
            "required": ["album_id"]
        }
    }
}

next_function = {
    "type": "function",
    "function": {
        "name": "next",
        "description": "Returns the next result given a paged result. If there is no next page, returns `None`.",
        "parameters": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "The result to get the next page of."
                }
            },
            "required": ["result"]
        }
    }
}

track_function = {
    "type": "function",
    "function": {
        "name": "track",
        "description": "Returns a single track given the track's ID, URI or URL",
        "parameters": {
            "type": "object",
            "properties": {
                "track_id": {
                    "type": "string",
                    "description": "The Spotify URI for the track. Example: spotify:track:4iV5W9uYEdYUVa79Axb7Rh"
                },
                "market": {
                    "type": "string",
                    "description": "An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking."
                }
            },
            "required": ["track_id"]
        }
    }
}

artist_function = {
    "type": "function",
    "function": {
        "name": "artist",
        "description": "Returns a single artist given the artist's ID, URI or URL",
        "parameters": {
            "type": "object",
            "properties": {
                "artist_id": {
                    "type": "string",
                    "description": "The Spotify URI for the artist. Example: spotify:artist:0LcJLqbBmaGUft1e9Mm8Cd"
                },
            },
            "required": ["artist_id"]
        }
    }
}

artist_albums_function = {
    "type": "function",
    "function": {
        "name": "artist_albums",
        "description": "Get Spotify catalog information about an artist's albums",
        "parameters": {
            "type": "object",
            "properties": {
                "artist_id": {
                    "type": "string",
                    "description": "The Spotify URI for the artist. Example: spotify:artist:0LcJLqbBmaGUft1e9Mm8Cd"
                },
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 50,
                    "description": "The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50."
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                    "minimum": 0,
                    "description": "The index of the first item to return. Default: 0 (the first item). Use with limit to get the next set of items."
                },
                "country": {
                    "type": "string",
                    "description": "An ISO 3166-1 alpha-2 country code or the string `from_token`. Provide this parameter if you want to apply Track Relinking."
                },
                "album_type": {
                    "type": "string",
                    "enum": ["album", "single", "compilation", "appears_on"],
                    "description": "The type of album. Allowed values: `album`, `single`, `compilation`, or `appears_on`."
                }
            },
            "required": ["artist_id"]
        }
    }
}

artist_top_tracks_function = {
    "type": "function",
    "function": {
        "name": "artist_top_tracks",
        "description": "Get Spotify catalog information about an artist's top tracks",
        "parameters": {
            "type": "object",
            "properties": {
                "artist_id": {
                    "type": "string",
                    "description": "The Spotify URI for the artist. Example: spotify:artist:0LcJLqbBmaGUft1e9Mm8Cd"
                },
                "country": {
                    "type": "string",
                    "description": "An ISO 3166-1 alpha-2 country code or the string `from_token`. Provide this parameter if you want to apply Track Relinking."
                }
            },
            "required": ["artist_id"]
        }
    }
}

current_playback_function = {
    "type": "function",
    "function": {
        "name": "current_playback",
        "description": "Get information about the user’s current playback state, including track or episode, progress, and active device.",
        "parameters": {
            "type": "object",
            "properties": {
                "market": {
                    "type": "string",
                    "description": "An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking."
                }
            },
            "required": []
        }
    }
}

next_track_function = {
    "type": "function",
    "function": {
        "name": "next_track",
        "description": "Skips to next track in the user’s queue.",
        "parameters": {
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "The id of the device this command is targeting. If not supplied, the user's currently active device is the target."
                }
            },
            "required": []
        }
    }
}

start_playback_function = {
    "type": "function",
    "function": {
        "name": "start_playback",
        "description": """ Start a new context or resume current playback on the user's active device. Provide a context_uri to start playback of an album, artist, or playlist.
Provide a uris list to start playback of one or more tracks.
Provide offset as {“position”: <int>} or {“uri”: “<track uri>”} to start playback at a particular offset.""",
        "parameters": {
            "type": "object",
            "properties": {
                "device_id": {
                    "type": "string",
                    "description": "The id of the device this command is targeting. If not supplied, the user's currently active device is the target."
                },
                "context_uri": {
                    "type": "string",
                    "description": "The context to play."
                },
                "uris": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": "The Spotify URI for the track. Example: spotify:track:4iV5W9uYEdYUVa79Axb7Rh"
                    },
                    "description": "The list of Spotify URIs to play."
                },
                "offset": {
                    "description": "The index of the item to start at (i.e., to offset into context). Default: 0 (the first item). Use with `uri` to play from a specific item.",
                    "oneOf": [
                        {
                            "type": "object",
                            "properties": {
                                "position": {
                                    "type": "integer"
                                }
                            },
                            "required": ["position"]
                        },
                        {
                            "type": "object",
                            "properties": {
                                "uri": {
                                    "type": "string",
                                    "description": "The Spotify URI for the track. Example: spotify:track:4iV5W9uYEdYUVa79Axb7Rh"
                                }
                            },
                            "required": ["uri"]
                        }
                    ]
                },
                "position_ms": {
                    "type": "integer"
                }
            },
            "required": []
        }
    }
}

search_function = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search for an item. Follows Spotify's search query syntax: https://developer.spotify.com/documentation/web-api/reference/search/",
        "parameters": {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "The search query's keywords (for example, 'remaster track:Doxy artist:Miles Davis')."
                },
                "type": {
                    "type": "string",
                    "enum": ["album", "artist", "playlist", "track", "show", "episode", "audiobook"],
                    "description": "The type of item to return. One of: `album`, `artist`, `playlist`, `track`, `show`, `episode`, or `audiobook`.",
                    "default": "track"
                },
                "limit": {
                    "type": "integer",
                    "description": "The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 50
                },
                "offset": {
                    "type": "integer",
                    "description": "The index of the first item to return. Default: 0 (the first item). Use with limit to get the next set of items.",
                    "default": 0,
                    "minimum": 0
                },
                "market": {
                    "type": "string",
                    "description": "An ISO 3166-1 alpha-2 country code or the string `from_token`. Provide this parameter if you want to apply Track Relinking."
                }
            }
        }
    }
}

mark_completed_function = {
    "type": "function",
    "function": {
        "name": "mark_completed",
        "description": "Mark an overall task as completed",   
    }
}

mark_error_function = {
    "type": "function",
    "function": {
        "name": "mark_error",
        "description": "Mark that an error occurred, preventing further progress on the task",   
    }
}

add_to_queue_function = {
    "type": "function",
    "function": {
        "name": "add_to_queue",
        "description": "Adds a song to the end of a user’s queue. If device A is currently playing music and you try to add to the queue and pass in the id for device B, you will get a ‘Player command failed: Restriction violated’ error. I therefore recommend leaving device_id as None so that the active device is targeted",
        "parameters": {
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "The Spotify URI for the track. Example: spotify:track:4iV5W9uYEdYUVa79Axb7Rh"
                },
                "device_id": {
                    "type": "string",
                    "description": "The id of the device this command is targeting. If not supplied, the user's currently active device is the target."
                }
            },
            "required": ["uri"]
        }
    }
}

playlist_function = {
    "type": "function",
    "function": {
        "name": "playlist",
        "description": "Returns a playlist given the playlist's ID, URI or URL",
        "parameters": {
            "type": "object",
            "properties": {
                "playlist_id": {
                    "type": "string",
                    "description": "The Spotify URI for the playlist. Example: spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
                },
                "market": {
                    "type": "string",
                    "description": "An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking."
                },
                "additional_types":  {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["track", "episode"]
                    }
                }
            },
            "required": ["playlist_id"]
        }
    }
}

playlist_items_function = {
    "type": "function",
    "function": {
        "name": "playlist_items",
        "description": "Get full details of the tracks or episodes of a Spotify playlist",
        "parameters": {
            "type": "object",
            "properties": {
                "playlist_id": {
                    "type": "string",
                    "description": "The Spotify URI for the playlist. Example: spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
                },
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                    "description": "An array of the fields to return. If omitted, all fields are returned."
                },
                "limit": {
                    "type": "integer",
                    "description": "The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 50
                },
                "offset": {
                    "type": "integer",
                    "description": "The index of the first item to return. Default: 0 (the first item). Use with limit to get the next set of items.",
                    "default": 0,
                    "minimum": 0
                },
                "market": {
                    "type": "string",
                    "description": "An ISO 3166-1 alpha-2 country code. Provide this parameter if you want to apply Track Relinking."
                }
            },
            "required": ["playlist_id"]
        }
    }
}

queue_function = {
    "type": "function",
    "function": {
        "name": "queue",
        "description": "Get the user’s current playback queue"
    }
}

current_user_playlists_function = {
    "type": "function",
    "function": {
        "name": "current_user_playlists",
        "description": "Get a list of the playlists owned or followed by the current Spotify user",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 50
                },
                "offset": {
                    "type": "integer",
                    "description": "The index of the first item to return. Default: 0 (the first item). Use with limit to get the next set of items.",
                    "default": 0,
                    "minimum": 0
                }
            }
        }
    }
}



tools = [
    artist_function,
    artist_top_tracks_function,
    current_playback_function,
    next_function,
    search_function,
    start_playback_function,
    album_function,
    next_track_function,
    track_function,
    artist_albums_function,
    mark_completed_function,
    mark_error_function,
    add_to_queue_function,
    playlist_function,
    playlist_items_function,
    queue_function,
    current_user_playlists_function]

class SpotifyExpert(Expert):
    scopes = [
        "user-read-playback-state",
        "user-modify-playback-state",
        "user-read-currently-playing",
        "app-remote-control",
        "streaming",
        "user-read-playback-position",
        "user-top-read",
        "user-read-recently-played",
        "user-read-playback-position"
    ]
    
    def __init__(self, assistant_id: Optional[str]=None):
        self.spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=' '.join(self.scopes)))

        super().__init__(tools=tools, prompt=f"""You are an expert in the Spotify API. You can call the following commands: 
                        {NEWLINE_CHARACTER.join(['- ' + tool["function"]["name"] for tool in tools])}
                        
                        Using these, you help users with their tasks. For example,
                        
                        === EXAMPLE 1 ===
                        User: Skip this song
                        Assistant: next_track()
                        User: "success"
                        Assistant: mark_completed()
                        
                        === Example 2 ===
                        User: Skip this song and play Drake's top song
                        Assistant: next_track()
                        User: "success"
                        Assistant: search(q='artist:Drake', type='artist')
                        User: [JSON omitted for brevity]
                        Assistant: artist_top_tracks(artist_id='3TVXtAsR1Inumwj472S9r4')
                        User: [JSON omitted for brevity]
                        Assistant: start_playback(uris=['spotify:track:4I4G0LD277PWvfblYtSf91', 'spotify:track:67nepsnrcZkowTxMWigSbb'])
                        User: "success"
                        Assistant: mark_completed()
                        
                        === Example 3 ===
                        User: Play some Metro Boomin
                        Assistant: search(q='Metro Boomin')
                        User: [JSON omitted for brevity]
                        Assistant: start_playback(uris=['spotify:artist:0iEtIxbK0KxaSlF7G42ZOp])
                        User: "success"
                        Assistant: mark_completed()
                         
                         """, assistant_id=assistant_id)
    
    def dispatcher(self, calls):
        ret = []
        
        for tool_call in calls:
            obj = {
                "tool_call_id": tool_call.id,
                "output": ""
            }
            
            print(tool_call)
            
            func = tool_call.function
            print(func)
            arguments = json.loads(func.arguments)
            if func.name == mark_completed_function["function"]["name"]:
                obj["output"] = "success"
                return ([obj], STATUS_COMPLETED)
            elif func.name == mark_error_function["function"]["name"]:
                obj["output"] = "marked error"
                return ([obj], STATUS_FAILURE)
            else:
                if func.name == artist_function["function"]["name"]:
                    obj["output"] = self.spotify_client.artist(**arguments)
                elif func.name == artist_top_tracks_function["function"]["name"]:
                    obj["output"] = self.spotify_client.artist_top_tracks(**arguments) 
                elif func.name == current_playback_function["function"]["name"]:
                    obj["output"] = self.spotify_client.current_user_playing_track() 
                elif func.name == next_function["function"]["name"]:
                    obj["output"] = self.spotify_client.next_track()
                elif func.name == search_function["function"]["name"]:
                    obj["output"] = self.spotify_client.search(**arguments)
                elif func.name == start_playback_function["function"]["name"]:
                    obj["output"] = self.spotify_client.start_playback(**arguments)
                elif func.name == album_function["function"]["name"]:
                    obj["output"] = self.spotify_client.album(**arguments)
                elif func.name == next_track_function["function"]["name"]:
                    obj["output"] = self.spotify_client.next_track()
                elif func.name ==  track_function["function"]["name"]:
                    obj["output"] = self.spotify_client.track(**arguments)
                elif func.name == artist_albums_function["function"]["name"]:
                    obj["output"] = self.spotify_client.artist_albums(**arguments)
                elif func.name == add_to_queue_function["function"]["name"]:
                    obj["output"] = self.spotify_client.add_to_queue(**arguments)
                elif func.name == playlist_function["function"]["name"]:
                    obj["output"] = self.spotify_client.playlist(**arguments)
                elif func.name == playlist_items_function["function"]["name"]:
                    obj["output"] = self.spotify_client.playlist_items(**arguments)
                elif func.name == queue_function["function"]["name"]:
                    obj["output"] = self.spotify_client.queue(**arguments)
                if obj["output"] is None:
                    obj["output"] = "success"
            
                obj["output"] = json.dumps(obj["output"])
            ret.append(obj)
            
        return (ret, STATUS_CONTINUE)