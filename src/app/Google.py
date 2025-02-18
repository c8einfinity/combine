from googlesearch import search

class Google:

    @staticmethod
    def search(query):
        """
        Search
        :param query:
        :return:
        """
        search_results = []
        for j in search(query, tld="co.in", num=10, stop=10, pause=2):
            search_results.append(j)

        return search_results


