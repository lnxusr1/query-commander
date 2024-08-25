import sys
import traceback
import logging
import json

from querycommander.core.config import settings as cfg
from querycommander.core.helpers import encrypt, generate_session_token
from querycommander.core.tokenizer import tokenizer

def process_request(request, response):

    logger = logging.getLogger("PAGE")
    logger.setLevel(cfg.log_level)

    command = str(request.json_data.get("command", "auth")).lower()
    logger.debug(f"[{request.host}] COMMAND: {command}")

    if command == "login":
        from querycommander.core.authenticator import authenticator

        #logger.debug(f"authenticator type = {cfg.sys_authenticator.get('type', 'local')}")
        #logger.debug(f"tokenizer type = {cfg.sys_tokenizer.get('type', 'local')}")
        #logger.debug(f"connections type = {cfg.sys_connections().get('type', 'config')}")

        username = str(request.json_data.get("username", "")).strip()[0:100]
        password = str(request.json_data.get("password", ""))[0:256]

        if authenticator.validate(username, password):

            if len(authenticator.roles) == 0:
                # No roles for this login.
                response.output({ "ok": False, "error": "No roles" })
                return

            tokenizer.set_username(username)
            tokenizer.set_remote_addr(request.host)
            tokenizer.set("username", username)
            tokenizer.set("roles", authenticator.roles)
            tokenizer.set("connections", tokenizer.connections())
            resp_data = { "ok": True, "username": tokenizer.username, "roles": authenticator.roles, "profiles": cfg.profiles, "web_socket": cfg.web_socket }

            resp_data["role_selected"] = authenticator.roles[0]
            tokenizer.set("role_selected", resp_data["role_selected"])
            resp_data["connections"] = tokenizer.connections()
            if len(resp_data["connections"]) == 0:
                response.output({ "ok": False, "error": "No connections." })
                return

            if authenticator.use_token:
                tokenizer.set(
                    "credentials", 
                    encrypt(
                        tokenizer.safe_password, 
                        json.dumps({ "username": str(username), "password": str(password)[0:256]})
                    )
                )

            #tokenizer.purge()
            tokenizer.token = generate_session_token() # Force a new token to be issued
            logger.debug(f"[{username}@{tokenizer.remote_addr}] Authentication complete, placing token - {tokenizer.token}")
            if not tokenizer.update():
                logger.error(f"[{username}@{tokenizer.remote_addr}] Unable to create token - {tokenizer.token}")
                response.output({ "ok": False, "error": "No token" })
                return

            logger.info(f"[{username}@{tokenizer.remote_addr}] Login successful - {tokenizer.token}")

            # If only 1 role then return connections
            response.output(resp_data)
            return
        else:
            logger.error(f"[{username}@{tokenizer.remote_addr}] Authentication failed - {tokenizer.token}")
            response.output({ "ok": False, "error": "Bad login" })
            return

    tokenizer.set_token(request.token)
    tokenizer.set_username(request.username)
    tokenizer.set_remote_addr(request.host)

    if command == "check":
        # check: allow browser to check if session is still valid (does not auto-extend session length)
        # check-init: same as "check" but if a valid token is found it auto-extends the session length
        if not tokenizer.validate():
            logger.info(f"[{tokenizer.remote_addr}] Invalid token - {tokenizer.token}")
            response.output({ "ok": False, "logout": True }, extend=False)
            return
        else:
            username = tokenizer.username
            if request.json_data.get("extend", False):
                logger.info(f"[{username}@{tokenizer.remote_addr}] Session extended - {tokenizer.token}")
                tokenizer.update() # Auto extend session
            else:
                logger.info(f"[{username}@{tokenizer.remote_addr}] Session check successful - {tokenizer.token}")
            
            response.output({ 
                "ok": True, 
                "username": username,
                #"roles": [tokenizer.role_selected], # tokenizer.roles as list
                #"role_selected": tokenizer.role_selected, 
                "connections": tokenizer.connections(),
                "profiles": cfg.profiles,
                "web_socket": cfg.web_socket
            }, extend=False)

            return

    # ==============================================================================================================================

    if not tokenizer.validate():
        username = tokenizer.username
        if username is None:
            logger.error(f"[{tokenizer.remote_addr}] Invalid token - {tokenizer.token}")
        else:
            logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Failed validation - {tokenizer.token}")
        response.output({ "ok": False, "logout": True, "message": "Not logged in." }, extend=False)
        return

    if command == "logout":
        logger.debug(f"[{tokenizer.username}@{tokenizer.remote_addr}] Attempting logout - {tokenizer.token}")
        tokenizer.remove()
        logger.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] Logout successful - {tokenizer.token}")
        response.output({ "ok": False, "logout": True, "message": "Logout successful." }, extend=False)
        return
    
    # ==============================================================================================================================
    # EVERYTHING BELOW THIS LINE MUST BE LOGGED IN WITH VALID TOKEN

    if command == "select-role":
        for role_name in tokenizer.roles:
            if role_name == str(request.json_data.get("role", "")):
                tokenizer.set("role_selected", role_name)
                tokenizer.update()
                logger.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] Role changed to {role_name} - {tokenizer.token}")
                response.output({ "ok": True, "connections": tokenizer.connections })
                return

        logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Role not found - {tokenizer.token}")
        response.output({ "ok": False })
        return

    if cfg.profiles:

        if command == "get-profile":
            try:
                prf = tokenizer.get_profiler()

                tabs = prf.get("tabs", [])
                page_settings = prf.get("settings", {})

                connection_details = {}

                if len(tabs) > 0:
                    from querycommander.functions.meta import get_info_dbs
                    for t in tabs:
                        c_name = t.get("connection")
                        if c_name in connection_details:
                            continue

                        logger.debug(c_name)
                        dbs = get_info_dbs(c_name)
                        if dbs is not None:
                            connection_details[c_name] = dbs

                logger.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] Profile retrieved - {tokenizer.token}")

                response.output({
                    "ok": True,
                    "tabs": tabs,
                    "settings": page_settings,
                    "connections": connection_details
                })

            except:
                logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Failed to get profile - {tokenizer.token}")
                logger.debug(str(sys.exc_info()[0]))
                logger.debug(str(traceback.format_exc()))
                response.output({ "ok": False })
            
            return

        if command == "save-profile":
            try:
                prf = tokenizer.get_profiler()

                prf.set("tabs", request.json_data.get("tabs", []))
                prf.set("settings", request.json_data.get("settings", {}))
                ret = prf.update()

                logger.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] Profile saved - {tokenizer.token}")

                response.output({
                    "ok": ret
                })

            except:
                logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Failed to save profile - {tokenizer.token}")
                logger.debug(str(sys.exc_info()[0]))
                logger.debug(str(traceback.format_exc()))
                response.output({ "ok": False })

            return

        if command == "delete-profile":
            try:
                prf = tokenizer.get_profiler()
                ret = prf.remove()

                logger.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] Profile deleted - {tokenizer.token}")

                response.output({
                    "ok": ret
                })

            except:
                logger.error(f"[{tokenizer.username}@{tokenizer.remote_addr}] Failed to delete profile - {tokenizer.token}")
                logger.debug(str(sys.exc_info()[0]))
                logger.debug(str(traceback.format_exc()))
                response.output({ "ok": False })

            return

    if command == "meta":
        #logger.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] meta request [{tokenizer.token}]")
        from querycommander.functions.meta import get_info
        return get_info(request, response, "meta")

    if command == "ddl":
        #logger.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] ddl request [{tokenizer.token}]")
        from querycommander.functions.meta import get_info
        return get_info(request, response, "ddl")

    if command == "details":
        #logger.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] detail request [{tokenizer.token}]")
        from querycommander.functions.meta import get_info
        return get_info(request, response, "details")

    if command == "query":
        #logger.info(f"[{tokenizer.username}@{tokenizer.remote_addr}] detail request [{tokenizer.token}]")
        from querycommander.functions.query import get_query_results
        return get_query_results(
            response, 
            request.json_data.get("connection"), 
            request.json_data.get("database"), 
            request.json_data.get("statement"), 
            request.json_data.get("type"),
            int(request.json_data.get("row_count", 0))
        )

    # Default response... not valid, client should initiate logout procedures
    logger.error(f"[{request.host}] Invalid request")
    response.output({ "ok": False, "logout": True })
    return
