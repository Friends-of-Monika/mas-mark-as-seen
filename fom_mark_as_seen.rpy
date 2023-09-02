# This file is the submod script of Mark as Seen submod by Friends of Monika.
# Please direct any issues and questions here (create an issue on GitHub):
# https://github.com/friends-of-monika/mas-mark-as-seen/issues


## HEADER

init -990 python in mas_submod_utils:

    Submod(
        author="Friends of Monika",
        name="Mark as Seen",
        description=_("Remove unwanted topics from Unseen menu"),
        version="1.0.0"
    )


init -989 python:

    if store.mas_submod_utils.isSubmodInstalled("Submod Updater Plugin"):
        store.sup_utils.SubmodUpdater(
            submod="Mark as Seen",
            user_name="Friends-of-Monika",
            repository_name="mas-mark-as-seen",
            update_dir=""
        )


## PERSISTENT VARIABLES

default persistent._fom_mark_as_seen_labels = dict()


## TOPICS

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="fom_mark_as_seen_show_check_menu",
            prompt="I would like to edit the 'Unseen' menu",
            category=["you"],
            pool=True,
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label fom_mark_as_seen_show_check_menu:
    m 1eud "Oh? {w=0.5}{nw}"
    extend 3hua "Of course, [mas_get_player_nickname()]! {w=0.3}Just tell me what you'd want to show or hide~"

    $ unseen_event_labels = fom_mark_as_seen.get_unseen_with_overrides()

    python:
        check_menu_items = list()
        for ev_label, override in unseen_event_labels.items():
            check_menu_items.append((
                mas_getEVLPropValue(ev_label, "prompt"), ev_label,
                override is None,
                True, False))

    show monika at t21
    call screen mas_check_scrollable_menu( \
        check_menu_items, \
        mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, \
        selected_button_prompt=_("Done."), default_button_prompt=_("Done."), \
        return_all=True)

    python:
        for ev_label, visible in _return.items():
            if not visible:
                fom_mark_as_seen.mark_as_seen(ev_label)
            else:
                fom_mark_as_seen.clear_label_override(ev_label)

    show monika at t11
    m 3esd "Alright, [mas_get_player_nickname()]!"
    m 1esa "Let me do something now.{w=0.5}.{w=0.5}.{nw}"
    m 3eub "Done~"

    # 'Unseen' button is hidden, there are no unseen topics, so let users
    # return that button by modifying what's shown or hidden
    if len(fom_mark_as_seen.get_actual_unseen_labels()) == 0:
        $ mas_showEVL("fom_mark_as_seen_show_check_menu", "EVE", unlock=True)

    # Remove the lingering garbage
    $ del override, unseen_event_labels, check_menu_items
    return


## CORE API & FRAMEWORK

init 10 python in fom_mark_as_seen:

    from store import persistent
    from store import mas_submod_utils, mas_override_label
    from store import mas_showEVL, mas_hideEVL
    from store.mas_submod_utils import functionplugin

    import functools


    # Dictionary with stored labels. Values represent the following states:
    # * no label=value mapping - default behaviour
    # * label=True - topic is force-hidden from the menu
    __labels_store = persistent._fom_mark_as_seen_labels


    # Sets label behaviour override (see notes above)
    def set_label_override(ev_label, hide):
        __labels_store[ev_label] = hide

    # Gets label behavior override
    def get_label_override(ev_label):
        return __labels_store.get(ev_label)

    # Gets all overides
    def get_label_overrides():
        return __labels_store.copy()

    # Clears the behaviour override on the label
    def clear_label_override(ev_label):
        __labels_store.pop(ev_label, None)

    # Convenience aliases
    mark_as_seen = functools.partial(set_label_override, hide=True)
    clear_mark = clear_label_override


    def get_force_display_labels():
        return __get_labels(False, must_exist=True)

    def get_force_hide_labels():
        return __get_labels(True, must_exist=True)

    def __get_labels(match_value, must_exist=False):
        filtered = [ev_label for ev_label, value in __labels_store.items()
                    if value == match_value]
        if must_exist:
            filtered = [ev_label for ev_label in filtered
                        if renpy.has_label(ev_label)]
        return filtered


    # This function below handles the Talk menu in such way that when there are
    # no unseen topics (after we have sifted out those that player chose to hide)
    # the Unseen button disappears; that's the length we have to go to do it
    # without copy-pasting the entire thing. It reverts upon exiting prompt menu.
    # Another task for it is to show or hide (by locking/unlocking) the topic
    # for changing the unseen menu.

    __renpy_display_menu = renpy.display_menu

    @functionplugin("prompt_menu")
    def __on_prompt_menu():
        def has_unseen_button(items):
            # Check if we have a button tuple with return value of 'Unseen' button
            return bool([retval for _, retval in items if retval == "unseen"])

        def intercept_renpy_display_menu(items, *args, **kwargs):
            try:
                # Bail out if we ended up in wrong label
                if mas_submod_utils.current_label != "prompt_menu":
                    return __renpy_display_menu(items, *args, **kwargs)

                # Pop the unseen button if menu has it and actually we have no
                # topics to show there (e.g. they're all hidden forcibly)
                unseen_count = len(get_actual_unseen_labels())
                if has_unseen_button(items) and unseen_count == 0:
                    items.pop(0)
                return __renpy_display_menu(items, *args, **kwargs)

            finally:
                # Revert to original function
                renpy.display_menu = __renpy_display_menu

        # Intercept the next call of display_menu
        renpy.display_menu = intercept_renpy_display_menu

        # Hide the 'show/hide' topic when there are no overrides or when there
        # is more than one unseen item shows up
        if len(get_actual_unseen_labels()) > 0 or len(__labels_store) == 0:
            mas_hideEVL("fom_mark_as_seen_show_check_menu", "EVE", lock=True)

    @functionplugin("prompt_menu_end")
    def __on_prompt_menu_end():
        # Revert back to normal function after exit
        renpy.display_menu = __renpy_display_menu


    # Override the label with our replacement label
    mas_override_label("show_prompt_list", "fom_mark_as_seen_show_prompt_list_override")


# BELOW CODE IS HEAVILY DEPENDENT ON event-handler.rpy, COMMIT 4d30921f (v0.12.14)
# UPDATE **EVERYTHING** BELOW ACCORDINGLY ON FURTHER UPDATES!

    def get_unseen_with_overrides():
        overrides = get_label_overrides()
        final_map = dict()

        for ev_label in get_mas_unseen_labels():
            final_map[ev_label] = overrides.get(ev_label, None)

        return final_map

    def get_mas_unseen_labels():
        from store import Event, mas_curr_affection
        from store import seen_event
        import store.evhand as evhand

        #Get list of unlocked prompts, sorted by unlock date
        unlocked_events = Event.filterEvents(
            evhand.event_database,
            unlocked=True,
            aff=mas_curr_affection
        )

        sorted_event_labels = Event.getSortedKeys(unlocked_events,include_none=True)
        unseen_event_labels = [
            ev_label
            for ev_label in sorted_event_labels
            if not seen_event(ev_label) and ev_label != "mas_show_unseen"
        ]

        return unseen_event_labels

    def get_actual_unseen_labels():
        from store import fom_mark_as_seen

        # Apply our own logic for force hide/force show labels
        display_labels = set(fom_mark_as_seen.get_force_display_labels())
        hide_labels = set(fom_mark_as_seen.get_force_hide_labels())

        # Remove hidden labels
        unseen_event_labels = [ev_label for ev_label in get_mas_unseen_labels()
            if ev_label not in hide_labels]

        for ev_label in display_labels:
            if ev_label in unseen_event_labels:
                continue
            unseen_event_labels.append(ev_label)

        return unseen_event_labels


# This exists just for injecting actual unseen labels into the prompt list screen.
label fom_mark_as_seen_show_prompt_list_override(sorted_event_labels):

    $ import store.evhand as evhand

    #Get list of unlocked prompts, sorted by unlock date
    python:
        prompt_menu_items = [
            (mas_getEVLPropValue(ev_label, "prompt"), ev_label, False, False)
            for ev_label in fom_mark_as_seen.get_actual_unseen_labels()
        ]

        final_items = (
            (_("I don't want to see this menu anymore"), "mas_hide_unseen", False, False, 20),
            (_("I don't want to see some of the topics"), "fom_mark_as_seen_show_check_menu", False, False, 0),
            (_("Nevermind"), False, False, False, 0)
        )

    call screen mas_gen_scrollable_menu(prompt_menu_items, mas_ui.SCROLLABLE_MENU_LOW_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, *final_items)

    if _return:
        $ mas_setEventPause(None)
        $ MASEventList.push(_return, skipeval=True)

    return _return
