import time
import asyncio
import logging
import aiohttp


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


async def make_req(delay):
    url = f"https://httpbin.org/delay/{delay}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return response.status


async def f(delay=0.5):
    logging.info("f is starting")
    result = await make_req(delay)
    logging.info("f finished")
    return result


async def g(delay=1):
    logging.info("g is starting")
    result = await make_req(delay)
    logging.info("g finished")
    return result


async def just_await():
    """
    - these coroutines DO NOT RUN concurrently.
    await_g only starts after await_f has finished
    - we cannot cancel them once we started awaiting

    so, this whole operation should take 3s
    """
    await f()
    await g()


async def wrapping_in_tasks():
    logging.info("wrapping_in_tasks running")
    """
    - wraps the coroutine in asyncio.Task
    - https://docs.python.org/3/library/asyncio-task.html#asyncio.Task
    - Tasks are used to run coroutines in event loops.

    """
    task_f = asyncio.create_task(f())
    task_g = asyncio.create_task(g())

    """
    f() and g() are already running at this point!

    time.sleep vs asyncio.sleep
    - time.sleep will block the entire execution, just frozen and do nothing
        - aka it will block the current thread
    - asyncio.sleep will ask the event loop to run something else
    while we wait for statement to finishes its execution
        - aka this won't block the execution of the script
    """
    await asyncio.sleep(0.1)

    """
    now our tasks are running concurrently
    if we don't want to run them, we can cancel them
    """
    task_f.cancel()
    try:
        await task_f
    except asyncio.CancelledError:
        logging.info("task_f is cancelled now")

    await task_g


async def gather_the_tasks():
    """
    asyncio.gather takes 1 or more awaitables as *args, wraps them in tasks
    if necessary and wait for all to finish
    then it reutnrs the results of all awaitables in the same order
    as we passed in the awaitables
    if gather is canclled, it cancels all unfinished tasks it is gathering

    this is how we wait for many awaitables at once.
    """
    result_f, result_g = await asyncio.gather(f(), g())


async def wait_for_tasks():
    """
    asyncio.wait_for makes sure the tasks are cancelled
    when it exceeds the timtout set
    it takes one awaitable
    """
    try:
        result_f, result_g = await asyncio.wait_for(
            asyncio.gather(f(), g()),
            timeout=3.0
        )
    except asyncio.TimeoutError:
        logging.exception("oops. it took longer than 4s!")


async def as_completed():
    """
    https://docs.python.org/3/library/asyncio-task.html#asyncio.as_completed
    - takes many awaitables in an iterable
    - yield futures that we have to await as long as something is done
    - takes an optional timeout
    """
    coros = [f(), g()]
    for fut in asyncio.as_completed(coros, timeout=3.0):
        try:
            await fut
            logging.info("one task down")
        except asyncio.TimeoutError:
            logging.exception("An exception happens!")


async def wait():
    """
    we can pass a timeout after which wait() will return.
    unlike gather(), nothing is done to the awaitables when that timeout
    expires.
    by default, we can tell wait() to not wait until all awaitables are done
    with "return_when" argument
    default is asyncio.ALL_COMPLETED

    - asyncio.FIRST_EXCEPTION - As soon as all are done,
    or as soon as one raises an exception
    - asyncio.FIRST_COMPLETED - As soon as any awaitable is done.

    https://docs.python.org/3/library/asyncio-task.html#asyncio.wait
    """
    task_f = asyncio.create_task(f())
    task_g = asyncio.create_task(g())
    done, pending = await asyncio.wait({task_f, task_g},
                                       return_when=asyncio.FIRST_EXCEPTION)
    for t in done:
        try:
            if t is task_f:
                logging.info(f"result of task_f {await task_f}")
        except Exception:
            logging.exception("f() failed")

    for t in done:
        try:
            if t is task_g:
                logging.info(f"result of task_g {await task_g}")
        except Exception:
            logging.exception("g() failed")


async def main():
    start = time.time()
    # await just_await()
    # await wrapping_in_tasks()
    # await gather_the_tasks()
    # await wait_for_tasks()
    # await as_completed()
    await wait()
    logging.info(f"finished in {time.time() - start}")


asyncio.run(main())
